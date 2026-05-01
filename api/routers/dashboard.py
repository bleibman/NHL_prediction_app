"""Dashboard API endpoints."""

from fastapi import APIRouter

from db.supabase import select, rpc
from api.schemas import DashboardSummary, StandingRow, ScorerRow
from api import cache

router = APIRouter()


def _format_season(s: int) -> str:
    return f"{s // 10000}\u2013{str(s // 10000 + 1)[-2:]}"


def _build_standings(rows: list[dict], teams_map: dict[int, str]) -> list[StandingRow]:
    result = []
    for row in rows:
        result.append(StandingRow(
            team=teams_map.get(row["team_id"], "?"),
            gp=row["games_played"],
            w=row["wins"],
            l=row["losses"],
            otl=row["ot_losses"],
            pts=row["points"],
            pts_pct=round((row.get("point_pct") or 0) * 100, 1),
            gf=row["goals_for"],
            ga=row["goals_against"],
            pp_pct=round((row.get("pp_pct") or 0) * 100, 1),
            pk_pct=round((row.get("pk_pct") or 0) * 100, 1),
            fo_pct=round((row.get("faceoff_pct") or 0) * 100, 1),
            sf_pg=round(row.get("shots_for_pg") or 0, 1),
            sa_pg=round(row.get("shots_against_pg") or 0, 1),
        ))
    return result


def _get_teams_map() -> dict[int, str]:
    cached = cache.get("teams_map")
    if cached is not None:
        return cached
    teams_map = {
        t["id"]: t["abbreviation"]
        for t in select("teams", columns="id,abbreviation")
    }
    cache.set("teams_map", teams_map, ttl=3600)
    return teams_map


@router.get("/summary", response_model=DashboardSummary)
def get_summary():
    cached = cache.get("dashboard_summary")
    if cached is not None:
        return cached

    data = rpc("get_dashboard_summary")
    if not data:
        return DashboardSummary(
            season_id=0, season_display="N/A",
            games_count=0, playoff_series_count=0, players_count=0,
        )

    result = DashboardSummary(
        season_id=data["season_id"],
        season_display=_format_season(data["season_id"]),
        games_count=data["games_count"],
        playoff_series_count=data["playoff_series_count"],
        players_count=data["players_count"],
    )
    cache.set("dashboard_summary", result)
    return result


@router.get("/standings", response_model=list[StandingRow])
def get_standings():
    cached = cache.get("dashboard_standings")
    if cached is not None:
        return cached

    seasons = select(
        "season_stats", columns="season_id", order="season_id.desc", limit=1
    )
    if not seasons:
        return []

    latest = int(seasons[0]["season_id"])
    stats = select(
        "season_stats",
        columns="team_id,games_played,wins,losses,ot_losses,points,"
        "goals_for,goals_against,pp_pct,pk_pct,faceoff_pct,"
        "point_pct,shots_for_pg,shots_against_pg",
        filters={"season_id": f"eq.{latest}"},
        order="points.desc",
    )
    result = _build_standings(stats, _get_teams_map())
    cache.set("dashboard_standings", result)
    return result


@router.get("/top-scorers", response_model=list[ScorerRow])
def get_top_scorers(limit: int = 10):
    cache_key = f"dashboard_scorers_{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    seasons = select(
        "season_stats", columns="season_id", order="season_id.desc", limit=1
    )
    if not seasons:
        return []

    latest = int(seasons[0]["season_id"])
    players = select(
        "player_stats",
        columns="player_name,team_abbrev,position,games_played,goals,assists,points",
        filters={"season_id": f"eq.{latest}"},
        order="points.desc",
        limit=limit,
    )
    result = [
        ScorerRow(
            player_name=p["player_name"],
            team=p["team_abbrev"],
            position=p["position"],
            gp=p["games_played"],
            goals=p["goals"],
            assists=p["assists"],
            points=p["points"],
        )
        for p in players
    ]
    cache.set(cache_key, result)
    return result
