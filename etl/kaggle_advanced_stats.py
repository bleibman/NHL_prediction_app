"""Import per-game advanced metrics from mexwell all_teams.csv into game_advanced_stats.

Phase 3: mexwell (2008-2022, MoneyPuck data, 5 situations per game per team)
"""

import csv
import logging
import os

from db.supabase import select, upsert
from etl.kaggle_mappings import normalize_moneypuck_abbrev

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MEXWELL_CSV = os.path.join(DATA_DIR, "mexwell", "all_teams.csv")


def _safe_int(val: str | None) -> int | None:
    if not val or val.strip().lower() in ("", "nan", "none"):
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


def import_advanced_stats(dry_run: bool = False) -> int:
    """Import advanced metrics from mexwell all_teams.csv."""
    if not os.path.isfile(MEXWELL_CSV):
        logger.warning("Mexwell CSV not found: %s", MEXWELL_CSV)
        return 0

    # Load valid game IDs from DB
    games = select("games", columns="id")
    valid_games: set[int] = {g["id"] for g in games}
    logger.info("DB has %d games for matching", len(valid_games))

    # Load team abbreviation → ID map from DB
    teams = select("teams", columns="id,abbreviation")
    abbrev_to_id: dict[str, int] = {t["abbreviation"]: t["id"] for t in teams}
    logger.info("Loaded %d team abbreviations", len(abbrev_to_id))

    matched = 0
    skipped = 0
    unmatched = 0
    rows: list[dict] = []

    with open(MEXWELL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_id = _safe_int(row.get("gameId"))
            if not game_id or game_id not in valid_games:
                skipped += 1
                continue

            # Resolve team abbreviation
            raw_abbrev = row.get("playerTeam", "").strip()
            abbrev = normalize_moneypuck_abbrev(raw_abbrev)
            team_id = abbrev_to_id.get(abbrev)
            if not team_id:
                unmatched += 1
                continue

            situation = row.get("situation", "").strip()
            if not situation:
                skipped += 1
                continue

            hoa = row.get("home_or_away", "").strip().upper()

            rows.append({
                "game_id": game_id,
                "team_id": team_id,
                "situation": situation,
                "is_home": hoa == "HOME",
                "x_goals_pct": _safe_float(row.get("xGoalsPercentage")),
                "corsi_pct": _safe_float(row.get("corsiPercentage")),
                "fenwick_pct": _safe_float(row.get("fenwickPercentage")),
                "ice_time": _safe_float(row.get("iceTime")),
                "x_goals_for": _safe_float(row.get("xGoalsFor")),
                "x_goals_against": _safe_float(row.get("xGoalsAgainst")),
                "goals_for": _safe_int(row.get("goalsFor")),
                "goals_against": _safe_int(row.get("goalsAgainst")),
                "shots_on_goal_for": _safe_int(row.get("shotsOnGoalFor")),
                "shots_on_goal_against": _safe_int(row.get("shotsOnGoalAgainst")),
                "shot_attempts_for": _safe_int(row.get("shotAttemptsFor")),
                "shot_attempts_against": _safe_int(row.get("shotAttemptsAgainst")),
                "high_danger_shots_for": _safe_int(row.get("highDangerShotsFor")),
                "high_danger_shots_against": _safe_int(row.get("highDangerShotsAgainst")),
                "high_danger_goals_for": _safe_int(row.get("highDangerGoalsFor")),
                "high_danger_goals_against": _safe_int(row.get("highDangerGoalsAgainst")),
                "high_danger_x_goals_for": _safe_float(row.get("highDangerxGoalsFor")),
                "high_danger_x_goals_against": _safe_float(row.get("highDangerxGoalsAgainst")),
                "medium_danger_shots_for": _safe_int(row.get("mediumDangerShotsFor")),
                "medium_danger_shots_against": _safe_int(row.get("mediumDangerShotsAgainst")),
                "low_danger_shots_for": _safe_int(row.get("lowDangerShotsFor")),
                "low_danger_shots_against": _safe_int(row.get("lowDangerShotsAgainst")),
                "faceoffs_won_for": _safe_int(row.get("faceOffsWonFor")),
                "faceoffs_won_against": _safe_int(row.get("faceOffsWonAgainst")),
                "hits_for": _safe_int(row.get("hitsFor")),
                "hits_against": _safe_int(row.get("hitsAgainst")),
                "takeaways_for": _safe_int(row.get("takeawaysFor")),
                "takeaways_against": _safe_int(row.get("takeawaysAgainst")),
                "giveaways_for": _safe_int(row.get("giveawaysFor")),
                "giveaways_against": _safe_int(row.get("giveawaysAgainst")),
                "penalties_for": _safe_int(row.get("penaltiesFor")),
                "penalties_against": _safe_int(row.get("penaltiesAgainst")),
                "penalty_minutes_for": _safe_int(row.get("penalityMinutesFor")),
                "penalty_minutes_against": _safe_int(row.get("penalityMinutesAgainst")),
            })
            matched += 1

            # Batch upsert every 5000 rows
            if len(rows) >= 5000:
                if not dry_run:
                    upsert("game_advanced_stats", rows, on_conflict="game_id,team_id,situation")
                rows = []

    # Final batch
    if rows and not dry_run:
        upsert("game_advanced_stats", rows, on_conflict="game_id,team_id,situation")

    logger.info(
        "Mexwell advanced stats: matched=%d, skipped=%d, unmatched=%d",
        matched, skipped, unmatched,
    )
    return matched
