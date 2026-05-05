"""Import per-game per-team box scores into game_team_stats.

Phase 2a: martinellis game_teams_stats.csv (2000-2020, NHL API IDs)
Phase 2b: coletti nhl_dataset.csv (2024-25, ESPN IDs)
"""

import csv
import logging
import os
from datetime import datetime

from db.supabase import select, upsert
from etl.kaggle_mappings import COLETTI_TEAM_ID_MAP

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MARTINELLIS_CSV = os.path.join(DATA_DIR, "game_teams_stats.csv")
COLETTI_CSV = os.path.join(DATA_DIR, "coletti", "nhl_dataset.csv")


def _safe_int(val: str | None) -> int | None:
    if not val or val.strip().lower() in ("", "nan", "none", "false", "true"):
        return None
    try:
        return int(float(val.strip()))
    except (ValueError, TypeError):
        return None


def _safe_float(val: str | None) -> float | None:
    if not val or val.strip().lower() in ("", "nan", "none"):
        return None
    try:
        return float(val.strip())
    except (ValueError, TypeError):
        return None


def _load_valid_game_ids() -> set[int]:
    """Return set of game IDs that exist in the DB."""
    games = select("games", columns="id")
    return {g["id"] for g in games}


def _load_valid_team_ids() -> set[int]:
    """Return set of team IDs that exist in the DB."""
    teams = select("teams", columns="id")
    return {t["id"] for t in teams}


def import_martinellis_team_stats(dry_run: bool = False) -> int:
    """Phase 2a: Import from martinellis game_teams_stats.csv."""
    if not os.path.isfile(MARTINELLIS_CSV):
        logger.warning("Martinellis CSV not found: %s", MARTINELLIS_CSV)
        return 0

    valid_games = _load_valid_game_ids()
    valid_teams = _load_valid_team_ids()
    logger.info("DB has %d games and %d teams for matching", len(valid_games), len(valid_teams))

    matched = 0
    skipped = 0
    rows: list[dict] = []

    with open(MARTINELLIS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_id = _safe_int(row.get("game_id"))
            team_id = _safe_int(row.get("team_id"))

            if not game_id or game_id not in valid_games:
                skipped += 1
                continue
            if not team_id or team_id not in valid_teams:
                skipped += 1
                continue

            hoa = row.get("HoA", "").strip().lower()
            won_raw = row.get("won", "").strip().upper()

            rows.append({
                "game_id": game_id,
                "team_id": team_id,
                "is_home": hoa == "home",
                "won": won_raw == "TRUE",
                "settled_in": row.get("settled_in", "").strip() or None,
                "goals": _safe_int(row.get("goals")),
                "shots": _safe_int(row.get("shots")),
                "hits": _safe_int(row.get("hits")),
                "pim": _safe_int(row.get("pim")),
                "power_play_opportunities": _safe_int(row.get("powerPlayOpportunities")),
                "power_play_goals": _safe_int(row.get("powerPlayGoals")),
                "faceoff_win_pct": _safe_float(row.get("faceOffWinPercentage")),
                "giveaways": _safe_int(row.get("giveaways")),
                "takeaways": _safe_int(row.get("takeaways")),
                "blocked": _safe_int(row.get("blocked")),
            })
            matched += 1

            # Batch upsert every 5000 rows
            if len(rows) >= 5000:
                if not dry_run:
                    upsert("game_team_stats", rows, on_conflict="game_id,team_id")
                rows = []

    # Final batch
    if rows and not dry_run:
        upsert("game_team_stats", rows, on_conflict="game_id,team_id")

    logger.info("Martinellis team stats: matched=%d, skipped=%d", matched, skipped)
    return matched


def import_coletti_team_stats(dry_run: bool = False) -> int:
    """Phase 2b: Import from coletti nhl_dataset.csv (2024-25, fills gaps)."""
    if not os.path.isfile(COLETTI_CSV):
        logger.warning("Coletti CSV not found: %s", COLETTI_CSV)
        return 0

    # Load game lookup by (date, home_team_id) since coletti uses ESPN game IDs
    games = select("games", columns="id,game_date,home_team_id,away_team_id")
    game_lookup: dict[tuple[str, int], dict] = {}
    for g in games:
        gd = g.get("game_date")
        ht = g.get("home_team_id")
        if gd and ht:
            game_lookup[(str(gd), ht)] = g

    # Load existing game_team_stats to avoid overwriting martinellis data
    existing = select("game_team_stats", columns="game_id,team_id")
    existing_pairs: set[tuple[int, int]] = {(r["game_id"], r["team_id"]) for r in existing}
    logger.info("Already have %d game_team_stats rows", len(existing_pairs))

    matched = 0
    skipped = 0
    unmatched = 0
    rows: list[dict] = []

    with open(COLETTI_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse date
            date_str = row.get("date", "")
            game_date = date_str[:10] if len(date_str) >= 10 else None
            if not game_date:
                skipped += 1
                continue

            # Map ESPN team_id → NHL team_id
            espn_id = _safe_int(row.get("team_id"))
            if not espn_id:
                skipped += 1
                continue
            nhl_team_id = COLETTI_TEAM_ID_MAP.get(espn_id)
            if not nhl_team_id:
                unmatched += 1
                continue

            # We need the home team to look up the game
            is_home = row.get("home_away") == "home"

            # For home rows, we can look up directly
            # For away rows, we need the opponent's ESPN ID to find the home team
            if is_home:
                home_team_id = nhl_team_id
            else:
                opp_espn_id = _safe_int(row.get("opp_team_id"))
                if not opp_espn_id:
                    skipped += 1
                    continue
                home_team_id = COLETTI_TEAM_ID_MAP.get(opp_espn_id)
                if not home_team_id:
                    unmatched += 1
                    continue

            game_info = game_lookup.get((game_date, home_team_id))
            if not game_info:
                unmatched += 1
                continue

            game_id = game_info["id"]

            # Skip if already covered by martinellis
            if (game_id, nhl_team_id) in existing_pairs:
                skipped += 1
                continue

            won_raw = row.get("won", "").strip()

            rows.append({
                "game_id": game_id,
                "team_id": nhl_team_id,
                "is_home": is_home,
                "won": won_raw == "1",
                "settled_in": None,  # coletti doesn't have this
                "goals": _safe_int(row.get("score")),
                "shots": _safe_int(row.get("shots")),
                "hits": _safe_int(row.get("hits")),
                "pim": _safe_int(row.get("pim")),
                "power_play_opportunities": _safe_int(row.get("power_play_opportunities")),
                "power_play_goals": _safe_int(row.get("power_play_goals")),
                "faceoff_win_pct": _safe_float(row.get("faceoff_win_pct")),
                "giveaways": _safe_int(row.get("giveaways")),
                "takeaways": _safe_int(row.get("takeaways")),
                "blocked": _safe_int(row.get("blocked_shots")),
            })
            existing_pairs.add((game_id, nhl_team_id))
            matched += 1

    if rows and not dry_run:
        upsert("game_team_stats", rows, on_conflict="game_id,team_id")

    logger.info(
        "Coletti team stats: matched=%d, skipped=%d, unmatched=%d",
        matched, skipped, unmatched,
    )
    return matched


def import_game_team_stats(dry_run: bool = False) -> dict[str, int]:
    """Run both team stats imports in order."""
    m_count = import_martinellis_team_stats(dry_run=dry_run)
    c_count = import_coletti_team_stats(dry_run=dry_run)
    return {"martinellis": m_count, "coletti": c_count}
