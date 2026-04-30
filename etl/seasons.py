"""Fetch and upsert season-level team stats."""

import logging

from config import LAST_SEASON
from db.supabase import select, upsert
from etl.api_client import get_stats

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


def fetch_and_upsert_seasons(single_season: int | None = None):
    """Pull team summary stats per season and upsert."""
    for sid in _season_range(single_season):
        logger.info("Fetching season stats for %d", sid)
        try:
            data = get_stats(
                "team/summary",
                params={"cayenneExp": f"seasonId={sid} and gameTypeId=2"},
            )
        except Exception:
            logger.warning("Failed to fetch season %d", sid, exc_info=True)
            continue

        # Auto-create any teams not yet in the DB (handles defunct/relocated teams)
        known_ids = {t["id"] for t in select("teams", columns="id")}
        missing_teams = []
        for t in data.get("data", []):
            tid = t.get("teamId")
            if tid and tid not in known_ids:
                name = t.get("teamFullName", f"Team {tid}")
                missing_teams.append({
                    "id": tid,
                    "abbreviation": name[:3].upper(),
                    "name": name,
                })
                known_ids.add(tid)
        if missing_teams:
            upsert("teams", missing_teams, on_conflict="id")
            logger.info("Auto-created %d historical teams", len(missing_teams))

        rows = []
        for t in data.get("data", []):
            team_id = t.get("teamId")
            if team_id is None:
                continue
            rows.append({
                "season_id": sid,
                "team_id": team_id,
                "games_played": t.get("gamesPlayed"),
                "wins": t.get("wins"),
                "losses": t.get("losses"),
                "ot_losses": t.get("otLosses"),
                "points": t.get("points"),
                "point_pct": t.get("pointPct"),
                "goals_for": t.get("goalsFor"),
                "goals_against": t.get("goalsAgainst"),
                "goals_for_pg": t.get("goalsForPerGame"),
                "goals_against_pg": t.get("goalsAgainstPerGame"),
                "pp_pct": t.get("powerPlayPct"),
                "pk_pct": t.get("penaltyKillPct"),
                "shots_for_pg": t.get("shotsForPerGame"),
                "shots_against_pg": t.get("shotsAgainstPerGame"),
                "faceoff_pct": t.get("faceoffWinPct"),
                "regulation_wins": t.get("winsInRegulation"),
                "shootout_wins": t.get("winsInShootout"),
            })

        if rows:
            upsert("season_stats", rows, on_conflict="season_id,team_id")
        logger.info("Upserted %d team records for season %d", len(rows), sid)
