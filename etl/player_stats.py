"""Fetch and upsert player stats."""

import logging

from config import LAST_SEASON
from db.supabase import upsert
from etl.api_client import get_stats
from etl.teams import get_team_abbrev_to_id_map

logger = logging.getLogger(__name__)

_PLAYER_LIMIT = 200  # top N per season


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


def fetch_and_upsert_player_stats(single_season: int | None = None):
    """Pull skater summary stats per season and upsert."""
    abbrev_map = get_team_abbrev_to_id_map()

    for sid in _season_range(single_season):
        logger.info("Fetching player stats for season %d", sid)
        try:
            data = get_stats(
                "skater/summary",
                params={
                    "cayenneExp": f"seasonId={sid} and gameTypeId=2",
                    "sort": '[{"property":"points","direction":"DESC"}]',
                    "limit": str(_PLAYER_LIMIT),
                },
            )
        except Exception:
            logger.warning("Failed player stats for season %d", sid, exc_info=True)
            continue

        rows: list[dict] = []
        for p in data.get("data", []):
            player_id = p.get("playerId")
            if not player_id:
                continue

            team_abbrevs = p.get("teamAbbrevs", "")
            # Player may have multiple teams; take last listed
            last_abbrev = team_abbrevs.split(",")[-1].strip() if team_abbrevs else ""
            team_id = abbrev_map.get(last_abbrev)

            rows.append({
                "player_id": player_id,
                "player_name": p.get("skaterFullName"),
                "season_id": sid,
                "team_id": team_id,
                "team_abbrev": last_abbrev or None,
                "position": p.get("positionCode"),
                "games_played": p.get("gamesPlayed"),
                "goals": p.get("goals"),
                "assists": p.get("assists"),
                "points": p.get("points"),
                "plus_minus": p.get("plusMinus"),
                "pim": p.get("penaltyMinutes"),
                "ev_goals": p.get("evGoals"),
                "ev_points": p.get("evPoints"),
                "pp_goals": p.get("ppGoals"),
                "pp_points": p.get("ppPoints"),
                "sh_goals": p.get("shGoals"),
                "sh_points": p.get("shPoints"),
                "game_winning_goals": p.get("gameWinningGoals"),
                "shots": p.get("shots"),
                "shooting_pct": p.get("shootingPct"),
                "toi_per_game": p.get("timeOnIcePerGame"),
            })

        if rows:
            upsert("player_stats", rows, on_conflict="player_id,season_id,team_abbrev")
        logger.info("Upserted %d player records for season %d", len(rows), sid)
