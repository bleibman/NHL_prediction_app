#!/usr/bin/env python3
"""One-time import of historical attendance data from Kaggle NHL Games CSV.

Usage:
    python scripts/import_attendance.py path/to/nhl_games.csv [--dry-run]

CSV source: Kaggle "NHL Games Database" by flynn28 (CC BY 4.0)
Expected columns: date (or game_date), home_team, attendance
"""

import argparse
import csv
import logging
import sys
import os
from datetime import datetime

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase import select, upsert

logger = logging.getLogger(__name__)

# Kaggle team names that differ from our DB team names
_KAGGLE_NAME_MAP: dict[str, str] = {
    "Montreal Canadiens": "Canadiens de Montréal",
    "Montréal Canadiens": "Canadiens de Montréal",
    "St. Louis Blues": "St. Louis Blues",
    "St Louis Blues": "St. Louis Blues",
}


def _parse_date(date_str: str) -> str | None:
    """Try multiple date formats and return YYYY-MM-DD or None."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _build_game_lookup(games: list[dict], teams_map: dict[int, str]) -> dict[tuple[str, int], int]:
    """Build (game_date, home_team_id) → game_id lookup."""
    lookup: dict[tuple[str, int], int] = {}
    for g in games:
        game_date = g.get("game_date")
        home_id = g.get("home_team_id")
        if game_date and home_id:
            lookup[(str(game_date), home_id)] = g["id"]
    return lookup


def import_attendance(csv_path: str, dry_run: bool = False):
    """Import attendance from Kaggle CSV into games table."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    logger.info("Loading teams from database...")
    teams = select("teams", columns="id,name")
    if not teams:
        logger.error("No teams in database — run teams ETL first")
        return

    # Build name → id map (case-insensitive)
    name_to_id: dict[str, int] = {}
    for t in teams:
        name_to_id[t["name"].lower()] = t["id"]

    logger.info("Loading games from database...")
    games = select("games", columns="id,game_date,home_team_id")
    if not games:
        logger.error("No games in database — run games ETL first")
        return

    game_lookup = _build_game_lookup(games, name_to_id)
    logger.info("Built lookup with %d games", len(game_lookup))

    # Detect CSV column names
    matched = 0
    skipped = 0
    unmatched = 0
    updates: list[dict] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        logger.info("CSV columns: %s", fieldnames)

        # Detect date column
        date_col = None
        for candidate in ("date", "game_date", "Date", "game_datetime_utc"):
            if candidate in fieldnames:
                date_col = candidate
                break
        if not date_col:
            logger.error("Cannot find date column in CSV. Columns: %s", fieldnames)
            return

        # Detect home team column
        home_col = None
        for candidate in ("home_team", "home_team_name", "Home Team", "home"):
            if candidate in fieldnames:
                home_col = candidate
                break
        if not home_col:
            logger.error("Cannot find home team column in CSV. Columns: %s", fieldnames)
            return

        # Detect attendance column
        att_col = None
        for candidate in ("attendance", "Attendance", "venue_capacity"):
            if candidate in fieldnames:
                att_col = candidate
                break
        if not att_col:
            logger.error("Cannot find attendance column in CSV. Columns: %s", fieldnames)
            return

        logger.info("Using columns: date=%s, home=%s, attendance=%s", date_col, home_col, att_col)

        for row in reader:
            raw_att = row.get(att_col, "").strip()
            if not raw_att or raw_att.lower() == "nan":
                skipped += 1
                continue

            try:
                attendance = int(float(raw_att))
            except (ValueError, TypeError):
                skipped += 1
                continue

            if attendance <= 0:
                skipped += 1
                continue

            # Parse date
            game_date = _parse_date(row.get(date_col, ""))
            if not game_date:
                skipped += 1
                continue

            # Resolve home team
            home_name = row.get(home_col, "").strip()
            home_name = _KAGGLE_NAME_MAP.get(home_name, home_name)
            home_team_id = name_to_id.get(home_name.lower())
            if not home_team_id:
                unmatched += 1
                continue

            # Look up game
            game_id = game_lookup.get((game_date, home_team_id))
            if not game_id:
                unmatched += 1
                continue

            updates.append({"id": game_id, "attendance": attendance})
            matched += 1

    logger.info(
        "Results: matched=%d, skipped=%d, unmatched=%d",
        matched, skipped, unmatched,
    )

    if dry_run:
        logger.info("DRY RUN — no database changes made")
        return

    if updates:
        upsert("games", updates, on_conflict="id")
        logger.info("Upserted %d attendance values", len(updates))
    else:
        logger.info("No attendance values to upsert")


def main():
    parser = argparse.ArgumentParser(
        description="Import attendance data from Kaggle NHL Games CSV"
    )
    parser.add_argument("csv_path", help="Path to the Kaggle NHL games CSV file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and match but don't write to database",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.csv_path):
        print(f"Error: file not found: {args.csv_path}", file=sys.stderr)
        sys.exit(1)

    import_attendance(args.csv_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
