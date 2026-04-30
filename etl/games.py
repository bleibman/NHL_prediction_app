"""Fetch and upsert game results."""

import logging

from config import LAST_SEASON
from db.supabase import select, upsert
from etl.api_client import get_web

logger = logging.getLogger(__name__)


def _season_range(single_season: int | None = None) -> list[int]:
    if single_season:
        return [single_season]
    seasons = []
    year = 2005
    while True:
        sid = year * 10000 + (year + 1)
        if sid > LAST_SEASON:
            break
        seasons.append(sid)
        year += 1
    return seasons


def fetch_and_upsert_games(single_season: int | None = None):
    """Pull game results per team/season and upsert."""
    teams = select("teams", columns="abbreviation")
    abbrevs = [t["abbreviation"] for t in teams]
    if not abbrevs:
        logger.warning("No teams in DB — run teams ETL first")
        return

    for sid in _season_range(single_season):
        seen_ids: set[int] = set()
        rows: list[dict] = []

        for abbrev in abbrevs:
            logger.debug("Fetching games for %s season %d", abbrev, sid)
            try:
                data = get_web(f"club-schedule-season/{abbrev}/{sid}")
            except Exception:
                logger.warning("Failed schedule for %s/%d", abbrev, sid, exc_info=True)
                continue

            for g in data.get("games", []):
                game_id = g.get("id")
                game_type = g.get("gameType")
                if game_type not in (2, 3):
                    continue
                if game_id in seen_ids:
                    continue
                seen_ids.add(game_id)

                state = g.get("gameState", "")
                if state not in ("FINAL", "OFF"):
                    continue

                home = g.get("homeTeam", {})
                away = g.get("awayTeam", {})
                outcome = g.get("gameOutcome", {})
                last_period = outcome.get("lastPeriodType", "REG")

                rows.append({
                    "id": game_id,
                    "season_id": sid,
                    "game_type": game_type,
                    "game_date": g.get("gameDate"),
                    "home_team_id": home.get("id"),
                    "away_team_id": away.get("id"),
                    "home_score": home.get("score"),
                    "away_score": away.get("score"),
                    "overtime": last_period in ("OT", "SO"),
                    "shootout": last_period == "SO",
                })

        if rows:
            upsert("games", rows, on_conflict="id")
        logger.info("Upserted %d games for season %d", len(rows), sid)
