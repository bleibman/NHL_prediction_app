"""Historical data API endpoints."""

from fastapi import APIRouter, HTTPException

from db.supabase import select
from api.schemas import StandingRow, ScorerRow, PlayoffSeriesRow, TeamTrendPoint

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


@router.get("/seasons", response_model=list[int])
def get_seasons():
    rows = select("season_stats", columns="season_id", order="season_id.asc")
    if not rows:
        return []
    return sorted(set(r["season_id"] for r in rows))


@router.get("/standings/{season_id}", response_model=list[StandingRow])
def get_standings(season_id: int):
    stats = select(
        "season_stats",
        columns="team_id,games_played,wins,losses,ot_losses,points,"
        "goals_for,goals_against,pp_pct,pk_pct,faceoff_pct,"
        "point_pct,shots_for_pg,shots_against_pg",
        filters={"season_id": f"eq.{season_id}"},
        order="points.desc",
    )
    teams_map = {
        t["id"]: t["abbreviation"]
        for t in select("teams", columns="id,abbreviation")
    }
    return _build_standings(stats, teams_map)


@router.get("/scorers/{season_id}", response_model=list[ScorerRow])
def get_scorers(season_id: int, limit: int = 50):
    players = select(
        "player_stats",
        columns="player_name,team_abbrev,position,games_played,"
        "goals,assists,points,plus_minus",
        filters={"season_id": f"eq.{season_id}"},
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
            plus_minus=p.get("plus_minus"),
        )
        for p in players
    ]


@router.get("/playoffs/{season_id}", response_model=list[PlayoffSeriesRow])
def get_playoffs(season_id: int):
    series = select(
        "playoff_series",
        columns="round,top_seed_id,bottom_seed_id,"
        "top_seed_wins,bottom_seed_wins,winning_team_id",
        filters={"season_id": f"eq.{season_id}"},
        order="round.asc",
    )
    if not series:
        return []

    teams_map = {
        t["id"]: t["abbreviation"]
        for t in select("teams", columns="id,abbreviation")
    }
    round_names = {1: "Round 1", 2: "Round 2", 3: "Conf. Finals", 4: "Stanley Cup Final"}

    result = []
    for s in series:
        top_abbrev = teams_map.get(s["top_seed_id"], "?")
        bot_abbrev = teams_map.get(s["bottom_seed_id"], "?")
        winner = teams_map.get(s["winning_team_id"]) if s["winning_team_id"] else None
        result.append(PlayoffSeriesRow(
            round_name=round_names.get(s["round"], "?"),
            matchup=f"{top_abbrev}  vs  {bot_abbrev}",
            score=f"{s['top_seed_wins']}\u2013{s['bottom_seed_wins']}",
            winner=winner,
        ))
    return result


@router.get("/team-trend/{team_abbrev}", response_model=list[TeamTrendPoint])
def get_team_trend(team_abbrev: str):
    teams = select("teams", columns="id,abbreviation")
    team_id = next(
        (t["id"] for t in teams if t["abbreviation"] == team_abbrev), None
    )
    if team_id is None:
        raise HTTPException(status_code=404, detail=f"Team '{team_abbrev}' not found")

    history = select(
        "season_stats",
        columns="season_id,wins,losses,points,goals_for,goals_against,point_pct",
        filters={"team_id": f"eq.{team_id}"},
        order="season_id.asc",
    )
    if not history:
        return []

    result = []
    for row in history:
        ga = row["goals_against"] if row["goals_against"] else 1
        result.append(TeamTrendPoint(
            season_id=row["season_id"],
            season_display=_format_season(row["season_id"]),
            wins=row["wins"],
            losses=row["losses"],
            points=row["points"],
            point_pct=round((row.get("point_pct") or 0) * 100, 1),
            gf_ga_ratio=round(row["goals_for"] / ga, 2),
        ))
    return result


@router.get("/teams", response_model=list[str])
def get_teams():
    teams = select("teams", columns="abbreviation")
    return sorted(t["abbreviation"] for t in teams)
