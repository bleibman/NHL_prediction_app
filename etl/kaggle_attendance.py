"""Import attendance data from Kaggle CSVs into games.attendance.

Phase 1a: coletti (2024-25, ESPN IDs, cleanest)
Phase 1b: flynn28 (2005-2025, team names, only fills NULLs)
"""

import csv
import logging
import os
from datetime import datetime

from db.supabase import select, upsert, update
from etl.kaggle_mappings import COLETTI_TEAM_ID_MAP, TEAM_NAME_TO_ID

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
COLETTI_CSV = os.path.join(DATA_DIR, "coletti", "nhl_dataset.csv")
FLYNN28_CSV = os.path.join(DATA_DIR, "flynn28", "data.csv")


def _load_game_lookup() -> tuple[dict[tuple[str, int], int], set[int]]:
    """Return (date,home_team_id)->game_id lookup and set of game_ids with attendance."""
    games = select("games", columns="id,game_date,home_team_id,attendance")
    lookup: dict[tuple[str, int], int] = {}
    has_attendance: set[int] = set()
    for g in games:
        gd = g.get("game_date")
        ht = g.get("home_team_id")
        if gd and ht:
            lookup[(str(gd), ht)] = g["id"]
            if g.get("attendance"):
                has_attendance.add(g["id"])
    return lookup, has_attendance


def _safe_int(val: str | None) -> int | None:
    """Parse a string to int, returning None for empty/NaN/invalid."""
    if not val or val.strip().lower() in ("", "nan", "none"):
        return None
    try:
        return int(float(val.strip()))
    except (ValueError, TypeError):
        return None


def import_coletti_attendance(dry_run: bool = False) -> int:
    """Phase 1a: Import attendance from coletti dataset (2024-25 season)."""
    if not os.path.isfile(COLETTI_CSV):
        logger.warning("Coletti CSV not found: %s", COLETTI_CSV)
        return 0

    logger.info("Loading game lookup from database...")
    game_lookup, _ = _load_game_lookup()
    logger.info("Game lookup has %d entries", len(game_lookup))

    matched = 0
    skipped = 0
    unmatched = 0
    updates: list[dict] = []

    with open(COLETTI_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only process home rows to avoid double-counting
            if row.get("home_away") != "home":
                continue

            attendance = _safe_int(row.get("attendance"))
            if not attendance or attendance <= 0:
                skipped += 1
                continue

            # Parse date (format: "2024-10-01 23:00:00+00:00")
            date_str = row.get("date", "")
            try:
                game_date = datetime.fromisoformat(date_str.replace("+00:00", "+00:00")).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                # Try just the date part
                game_date = date_str[:10] if len(date_str) >= 10 else None

            if not game_date:
                skipped += 1
                continue

            # Map ESPN team_id → NHL API team_id
            espn_id = _safe_int(row.get("team_id"))
            if not espn_id:
                skipped += 1
                continue
            nhl_team_id = COLETTI_TEAM_ID_MAP.get(espn_id)
            if not nhl_team_id:
                unmatched += 1
                continue

            # Look up game
            game_id = game_lookup.get((game_date, nhl_team_id))
            if not game_id:
                unmatched += 1
                continue

            updates.append({"id": game_id, "attendance": attendance})
            matched += 1

    logger.info(
        "Coletti attendance: matched=%d, skipped=%d, unmatched=%d",
        matched, skipped, unmatched,
    )

    if dry_run:
        logger.info("DRY RUN — no database changes")
        return matched

    if updates:
        for row in updates:
            update("games", {"attendance": row["attendance"]}, {"id": f"eq.{row['id']}"})
        logger.info("Updated %d coletti attendance values", len(updates))
    return matched


def import_flynn28_attendance(dry_run: bool = False) -> int:
    """Phase 1b: Import attendance from flynn28 (only where attendance IS NULL)."""
    if not os.path.isfile(FLYNN28_CSV):
        logger.warning("Flynn28 CSV not found: %s", FLYNN28_CSV)
        return 0

    logger.info("Loading game lookup from database...")
    game_lookup, has_attendance = _load_game_lookup()
    logger.info("Game lookup has %d entries, %d already have attendance",
                len(game_lookup), len(has_attendance))

    matched = 0
    skipped = 0
    unmatched = 0
    updates: list[dict] = []

    with open(FLYNN28_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip pre-2005 data (teams not in DB)
            date_str = row.get("Date", "")
            if not date_str or date_str < "2005-":
                skipped += 1
                continue

            attendance = _safe_int(row.get("Attendance"))
            if not attendance or attendance <= 0:
                skipped += 1
                continue

            # Parse date
            game_date = date_str[:10] if len(date_str) >= 10 else None
            if not game_date:
                skipped += 1
                continue

            # Resolve home team
            home_name = row.get("Home", "").strip()
            nhl_team_id = TEAM_NAME_TO_ID.get(home_name)
            if not nhl_team_id:
                unmatched += 1
                continue

            # Look up game
            game_id = game_lookup.get((game_date, nhl_team_id))
            if not game_id:
                unmatched += 1
                continue

            # Only fill NULLs — don't overwrite coletti data
            if game_id in has_attendance:
                skipped += 1
                continue

            updates.append({"id": game_id, "attendance": attendance})
            has_attendance.add(game_id)  # Track so we don't duplicate within flynn28
            matched += 1

    logger.info(
        "Flynn28 attendance: matched=%d, skipped=%d, unmatched=%d",
        matched, skipped, unmatched,
    )

    if dry_run:
        logger.info("DRY RUN — no database changes")
        return matched

    if updates:
        for row in updates:
            update("games", {"attendance": row["attendance"]}, {"id": f"eq.{row['id']}"})
        logger.info("Updated %d flynn28 attendance values", len(updates))
    return matched


def import_attendance(dry_run: bool = False) -> dict[str, int]:
    """Run both attendance imports in order. Returns counts per source."""
    coletti_count = import_coletti_attendance(dry_run=dry_run)
    flynn28_count = import_flynn28_attendance(dry_run=dry_run)
    return {"coletti": coletti_count, "flynn28": flynn28_count}
