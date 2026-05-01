"""Dashboard API endpoints."""

from fastapi import APIRouter

from db.supabase import select, rpc
from api.schemas import DashboardSummary, DashboardInit, StandingRow, ScorerRow
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


def _get_teams_full() -> list[dict]:
    """Return full teams list with division/conference info."""
    cached = cache.get("teams_full")
    if cached is not None:
        return cached
    teams = select("teams", columns="id,abbreviation,name,division,conference")
    cache.set("teams_full", teams, ttl=3600)
    return teams


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


@router.get("/seasons", response_model=list[int])
def get_seasons():
    cached = cache.get("dashboard_seasons")
    if cached is not None:
        return cached

    rows = select("season_stats", columns="season_id", order="season_id.desc")
    if not rows:
        return []
    result = sorted(set(r["season_id"] for r in rows), reverse=True)
    cache.set("dashboard_seasons", result)
    return result


@router.get("/divisions", response_model=list[str])
def get_divisions():
    cached = cache.get("dashboard_divisions")
    if cached is not None:
        return cached

    teams = _get_teams_full()
    divisions = sorted(set(t["division"] for t in teams if t.get("division")))
    cache.set("dashboard_divisions", divisions)
    return divisions


@router.get("/standings", response_model=list[StandingRow])
def get_standings(
    season_id: int | None = None,
    division: str | None = None,
    team: str | None = None,
):
    cache_key = f"dashboard_standings_{season_id}_{division}_{team}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Determine which season to use
    if season_id is None:
        seasons = select(
            "season_stats", columns="season_id", order="season_id.desc", limit=1
        )
        if not seasons:
            return []
        season_id = int(seasons[0]["season_id"])

    stats = select(
        "season_stats",
        columns="team_id,games_played,wins,losses,ot_losses,points,"
        "goals_for,goals_against,pp_pct,pk_pct,faceoff_pct,"
        "point_pct,shots_for_pg,shots_against_pg",
        filters={"season_id": f"eq.{season_id}"},
        order="points.desc",
    )

    teams_map = _get_teams_map()

    # Filter by division or specific team
    if division or team:
        teams_full = _get_teams_full()
        if division:
            allowed_ids = {t["id"] for t in teams_full if t.get("division") == division}
            stats = [s for s in stats if s["team_id"] in allowed_ids]
        elif team:
            # team is an abbreviation
            allowed_ids = {t["id"] for t in teams_full if t.get("abbreviation") == team}
            stats = [s for s in stats if s["team_id"] in allowed_ids]

    result = _build_standings(stats, teams_map)
    cache.set(cache_key, result)
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


@router.get("/init", response_model=DashboardInit)
def get_init():
    """Return all data the dashboard needs in a single round-trip."""
    cached = cache.get("dashboard_init")
    if cached is not None:
        return cached

    summary = get_summary()
    standings = get_standings()
    scorers = get_top_scorers()
    seasons = get_seasons()
    divisions = get_divisions()
    teams_full = _get_teams_full()
    teams = sorted(t["abbreviation"] for t in teams_full if t.get("abbreviation"))
    team_divisions = {
        t["abbreviation"]: t["division"]
        for t in teams_full
        if t.get("abbreviation") and t.get("division")
    }

    result = DashboardInit(
        summary=summary,
        standings=standings,
        scorers=scorers,
        seasons=seasons,
        divisions=divisions,
        teams=teams,
        team_divisions=team_divisions,
    )
    cache.set("dashboard_init", result)
    return result
