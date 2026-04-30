"""Fetch and upsert playoff series data."""

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


def fetch_and_upsert_playoffs(single_season: int | None = None):
    """Pull playoff bracket per season and upsert series data."""
    for sid in _season_range(single_season):
        logger.info("Fetching playoff bracket for %d", sid)
        try:
            data = get_web(f"playoff-series/carousel/{sid}/")
        except Exception:
            logger.warning("No playoff data for season %d", sid, exc_info=True)
            continue

        # Auto-create any teams not yet in the DB
        known_ids = {t["id"] for t in select("teams", columns="id")}
        missing_teams = []
        for rnd in data.get("rounds", []):
            for s in rnd.get("series", []):
                for seed in (s.get("topSeed", {}), s.get("bottomSeed", {})):
                    tid = seed.get("id")
                    abbrev = seed.get("abbrev", "")
                    if tid and tid not in known_ids:
                        missing_teams.append({
                            "id": tid,
                            "abbreviation": abbrev or str(tid)[:3],
                            "name": abbrev or f"Team {tid}",
                        })
                        known_ids.add(tid)
        if missing_teams:
            upsert("teams", missing_teams, on_conflict="id")
            logger.info("Auto-created %d teams from playoff data", len(missing_teams))

        rows: list[dict] = []
        for rnd in data.get("rounds", []):
            round_num = rnd.get("roundNumber")
            for s in rnd.get("series", []):
                top = s.get("topSeed", {})
                bottom = s.get("bottomSeed", {})
                if not top.get("id") or not bottom.get("id"):
                    continue

                rows.append({
                    "season_id": sid,
                    "round": round_num,
                    "series_letter": s.get("seriesLetter"),
                    "top_seed_id": top["id"],
                    "bottom_seed_id": bottom["id"],
                    "top_seed_wins": top.get("wins", 0),
                    "bottom_seed_wins": bottom.get("wins", 0),
                    "winning_team_id": s.get("winningTeamId"),
                    "losing_team_id": s.get("losingTeamId"),
                })

        if rows:
            upsert("playoff_series", rows, on_conflict="season_id,series_letter")
        logger.info("Upserted %d playoff series for season %d", len(rows), sid)
