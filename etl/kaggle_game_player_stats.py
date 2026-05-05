"""Import per-game player stats from martinellis CSVs.

Phase 4a: game_skater_stats.csv (945k rows)
Phase 4b: game_goalie_stats.csv (56k rows)

These are large imports — opt-in only (--player-stats-only or --all).
"""

import csv
import logging
import os

from db.supabase import select, upsert

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SKATER_CSV = os.path.join(DATA_DIR, "game_skater_stats.csv")
GOALIE_CSV = os.path.join(DATA_DIR, "game_goalie_stats.csv")


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


def import_skater_stats(dry_run: bool = False) -> int:
    """Phase 4a: Import per-game skater stats (945k rows)."""
    if not os.path.isfile(SKATER_CSV):
        logger.warning("Skater stats CSV not found: %s", SKATER_CSV)
        return 0

    # Load valid game and team IDs
    games = select("games", columns="id")
    valid_games: set[int] = {g["id"] for g in games}
    teams = select("teams", columns="id")
    valid_teams: set[int] = {t["id"] for t in teams}
    logger.info("DB has %d games and %d teams for skater matching", len(valid_games), len(valid_teams))

    matched = 0
    skipped = 0
    rows: list[dict] = []

    with open(SKATER_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_id = _safe_int(row.get("game_id"))
            team_id = _safe_int(row.get("team_id"))
            player_id = _safe_int(row.get("player_id"))

            if not game_id or game_id not in valid_games:
                skipped += 1
                continue
            if not team_id or team_id not in valid_teams:
                skipped += 1
                continue
            if not player_id:
                skipped += 1
                continue

            rows.append({
                "game_id": game_id,
                "player_id": player_id,
                "team_id": team_id,
                "time_on_ice": _safe_int(row.get("timeOnIce")),
                "goals": _safe_int(row.get("goals")),
                "assists": _safe_int(row.get("assists")),
                "shots": _safe_int(row.get("shots")),
                "hits": _safe_int(row.get("hits")),
                "power_play_goals": _safe_int(row.get("powerPlayGoals")),
                "power_play_assists": _safe_int(row.get("powerPlayAssists")),
                "penalty_minutes": _safe_int(row.get("penaltyMinutes")),
                "faceoff_wins": _safe_int(row.get("faceOffWins")),
                "faceoff_taken": _safe_int(row.get("faceoffTaken")),
                "takeaways": _safe_int(row.get("takeaways")),
                "giveaways": _safe_int(row.get("giveaways")),
                "short_handed_goals": _safe_int(row.get("shortHandedGoals")),
                "short_handed_assists": _safe_int(row.get("shortHandedAssists")),
                "blocked": _safe_int(row.get("blocked")),
                "plus_minus": _safe_int(row.get("plusMinus")),
                "even_time_on_ice": _safe_int(row.get("evenTimeOnIce")),
                "short_handed_time_on_ice": _safe_int(row.get("shortHandedTimeOnIce")),
                "power_play_time_on_ice": _safe_int(row.get("powerPlayTimeOnIce")),
            })
            matched += 1

            # Batch upsert every 5000 rows
            if len(rows) >= 5000:
                if not dry_run:
                    upsert("game_skater_stats", rows, on_conflict="game_id,player_id")
                logger.info("Skater stats progress: %d rows processed", matched)
                rows = []

    if rows and not dry_run:
        upsert("game_skater_stats", rows, on_conflict="game_id,player_id")

    logger.info("Skater stats: matched=%d, skipped=%d", matched, skipped)
    return matched


def import_goalie_stats(dry_run: bool = False) -> int:
    """Phase 4b: Import per-game goalie stats (56k rows)."""
    if not os.path.isfile(GOALIE_CSV):
        logger.warning("Goalie stats CSV not found: %s", GOALIE_CSV)
        return 0

    games = select("games", columns="id")
    valid_games: set[int] = {g["id"] for g in games}
    teams = select("teams", columns="id")
    valid_teams: set[int] = {t["id"] for t in teams}
    logger.info("DB has %d games and %d teams for goalie matching", len(valid_games), len(valid_teams))

    matched = 0
    skipped = 0
    rows: list[dict] = []

    with open(GOALIE_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_id = _safe_int(row.get("game_id"))
            team_id = _safe_int(row.get("team_id"))
            player_id = _safe_int(row.get("player_id"))

            if not game_id or game_id not in valid_games:
                skipped += 1
                continue
            if not team_id or team_id not in valid_teams:
                skipped += 1
                continue
            if not player_id:
                skipped += 1
                continue

            decision_raw = row.get("decision", "").strip()
            decision = decision_raw if decision_raw in ("W", "L", "O") else None

            rows.append({
                "game_id": game_id,
                "player_id": player_id,
                "team_id": team_id,
                "time_on_ice": _safe_int(row.get("timeOnIce")),
                "assists": _safe_int(row.get("assists")),
                "goals": _safe_int(row.get("goals")),
                "pim": _safe_int(row.get("pim")),
                "shots_against": _safe_int(row.get("shots")),
                "saves": _safe_int(row.get("saves")),
                "power_play_saves": _safe_int(row.get("powerPlaySaves")),
                "short_handed_saves": _safe_int(row.get("shortHandedSaves")),
                "even_saves": _safe_int(row.get("evenSaves")),
                "short_handed_shots_against": _safe_int(row.get("shortHandedShotsAgainst")),
                "even_shots_against": _safe_int(row.get("evenShotsAgainst")),
                "power_play_shots_against": _safe_int(row.get("powerPlayShotsAgainst")),
                "decision": decision,
                "save_pct": _safe_float(row.get("savePercentage")),
                "power_play_save_pct": _safe_float(row.get("powerPlaySavePercentage")),
                "even_strength_save_pct": _safe_float(row.get("evenStrengthSavePercentage")),
            })
            matched += 1

            if len(rows) >= 5000:
                if not dry_run:
                    upsert("game_goalie_stats", rows, on_conflict="game_id,player_id")
                logger.info("Goalie stats progress: %d rows processed", matched)
                rows = []

    if rows and not dry_run:
        upsert("game_goalie_stats", rows, on_conflict="game_id,player_id")

    logger.info("Goalie stats: matched=%d, skipped=%d", matched, skipped)
    return matched


def import_player_stats(dry_run: bool = False) -> dict[str, int]:
    """Run both player stats imports."""
    skater_count = import_skater_stats(dry_run=dry_run)
    goalie_count = import_goalie_stats(dry_run=dry_run)
    return {"skaters": skater_count, "goalies": goalie_count}
