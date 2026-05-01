"""Dashboard API endpoints."""

from fastapi import APIRouter

from db.supabase import select
from api.schemas import DashboardSummary, StandingRow, ScorerRow

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


@router.get("/summary", response_model=DashboardSummary)
def get_summary():
    seasons = select(
        "season_stats", columns="season_id", order="season_id.desc", limit=1
    )
    if not seasons:
        return DashboardSummary(
            season_id=0, season_display="N/A",
            games_count=0, playoff_series_count=0, players_count=0,
        )

    latest = int(seasons[0]["season_id"])
    games = select("games", columns="id", filters={"season_id": f"eq.{latest}"})
    playoffs = select(
        "playoff_series", columns="id", filters={"season_id": f"eq.{latest}"}
    )
    players = select(
        "player_stats", columns="id", filters={"season_id": f"eq.{latest}"}
    )

    return DashboardSummary(
        season_id=latest,
        season_display=_format_season(latest),
        games_count=len(games),
        playoff_series_count=len(playoffs),
        players_count=len(players),
    )


@router.get("/standings", response_model=list[StandingRow])
def get_standings():
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
    teams_map = {
        t["id"]: t["abbreviation"]
        for t in select("teams", columns="id,abbreviation")
    }
    return _build_standings(stats, teams_map)


@router.get("/top-scorers", response_model=list[ScorerRow])
def get_top_scorers(limit: int = 10):
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
    return [
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
