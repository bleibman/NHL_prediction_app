"""Ticket analytics API endpoints."""

from fastapi import APIRouter

import pandas as pd

from db.supabase import select
from api.schemas import (
    TicketSummary,
    UpcomingGame,
    PriceTrendPoint,
    TeamPrice,
    AttendancePoint,
)

router = APIRouter()


def _format_season(s: int) -> str:
    return f"{s // 10000}\u2013{str(s // 10000 + 1)[-2:]}"


def _load_snapshots():
    snapshots = select(
        "ticket_snapshots",
        columns="seatgeek_event_id,game_date,home_team_id,away_team_id,"
        "snapshot_date,lowest_price,average_price,highest_price,listing_count",
        order="game_date.asc",
    )
    teams_list = select("teams", columns="id,name,abbreviation")
    teams_map = {t["id"]: t["abbreviation"] for t in teams_list}
    return snapshots, teams_map


@router.get("/summary", response_model=TicketSummary)
def get_summary():
    snapshots, _ = _load_snapshots()
    if not snapshots:
        return TicketSummary(
            avg_price=None, lowest_price=None,
            total_listings=None, games_tracked=0, snapshot_date=None,
        )

    snap_df = pd.DataFrame(snapshots)
    latest_date = snap_df["snapshot_date"].max()
    latest = snap_df[snap_df["snapshot_date"] == latest_date]

    avg_ticket = latest["average_price"].mean()
    lowest_avail = latest["lowest_price"].min()
    total_listings = latest["listing_count"].sum()

    return TicketSummary(
        avg_price=round(float(avg_ticket), 0) if pd.notna(avg_ticket) else None,
        lowest_price=int(lowest_avail) if pd.notna(lowest_avail) else None,
        total_listings=int(total_listings) if pd.notna(total_listings) else None,
        games_tracked=len(latest),
        snapshot_date=str(latest_date),
    )


@router.get("/upcoming", response_model=list[UpcomingGame])
def get_upcoming():
    snapshots, teams_map = _load_snapshots()
    if not snapshots:
        return []

    snap_df = pd.DataFrame(snapshots)
    latest_date = snap_df["snapshot_date"].max()
    latest = snap_df[snap_df["snapshot_date"] == latest_date]

    result = []
    for _, row in latest.iterrows():
        game_date = pd.to_datetime(row["game_date"])
        result.append(UpcomingGame(
            date=game_date.strftime("%b %d, %Y"),
            home_team=teams_map.get(row["home_team_id"], "?"),
            away_team=teams_map.get(row["away_team_id"], "?"),
            avg_price=int(row["average_price"]) if pd.notna(row["average_price"]) else None,
            low_price=int(row["lowest_price"]) if pd.notna(row["lowest_price"]) else None,
            high_price=int(row["highest_price"]) if pd.notna(row["highest_price"]) else None,
            listings=int(row["listing_count"]) if pd.notna(row["listing_count"]) else None,
        ))
    result.sort(key=lambda g: g.date)
    return result


@router.get("/price-trends", response_model=list[PriceTrendPoint])
def get_price_trends():
    snapshots, _ = _load_snapshots()
    if not snapshots:
        return []

    snap_df = pd.DataFrame(snapshots)
    if snap_df["snapshot_date"].nunique() < 2:
        return []

    snap_df["game_date"] = pd.to_datetime(snap_df["game_date"])
    snap_df["snapshot_date"] = pd.to_datetime(snap_df["snapshot_date"])
    snap_df["days_until_game"] = (snap_df["game_date"] - snap_df["snapshot_date"]).dt.days
    snap_df = snap_df[snap_df["days_until_game"] >= 0]

    if snap_df.empty:
        return []

    avg_by_days = (
        snap_df.groupby("days_until_game")["average_price"]
        .mean()
        .reset_index()
        .sort_values("days_until_game")
    )
    return [
        PriceTrendPoint(
            days_until_game=int(row["days_until_game"]),
            average_price=round(float(row["average_price"]), 2),
        )
        for _, row in avg_by_days.iterrows()
    ]


@router.get("/team-prices", response_model=list[TeamPrice])
def get_team_prices():
    snapshots, teams_map = _load_snapshots()
    if not snapshots:
        return []

    snap_df = pd.DataFrame(snapshots)
    latest_date = snap_df["snapshot_date"].max()
    latest = snap_df[snap_df["snapshot_date"] == latest_date]

    team_prices = (
        latest.groupby("home_team_id")["average_price"]
        .mean()
        .reset_index()
        .sort_values("average_price", ascending=True)
    )
    team_prices["team"] = team_prices["home_team_id"].map(teams_map)
    team_prices = team_prices.dropna(subset=["team", "average_price"])

    return [
        TeamPrice(
            team=row["team"],
            average_price=round(float(row["average_price"]), 2),
        )
        for _, row in team_prices.iterrows()
    ]


@router.get("/attendance", response_model=list[AttendancePoint])
def get_attendance(team_abbrev: str | None = None):
    attendance_games = select(
        "games",
        columns="home_team_id,season_id,attendance",
        filters={"attendance": "not.is.null"},
    )
    if not attendance_games:
        return []

    teams = select("teams", columns="id,abbreviation")
    teams_map = {t["id"]: t["abbreviation"] for t in teams}

    att_df = pd.DataFrame(attendance_games)
    att_df["team"] = att_df["home_team_id"].map(teams_map)

    if team_abbrev:
        att_df = att_df[att_df["team"] == team_abbrev]

    if att_df.empty:
        return []

    season_avg = (
        att_df.groupby("season_id")["attendance"]
        .mean()
        .reset_index()
        .sort_values("season_id")
    )
    return [
        AttendancePoint(
            season_id=int(row["season_id"]),
            season_display=_format_season(int(row["season_id"])),
            avg_attendance=round(float(row["attendance"]), 0),
        )
        for _, row in season_avg.iterrows()
    ]


@router.get("/attendance-teams", response_model=list[str])
def get_attendance_teams():
    attendance_games = select(
        "games",
        columns="home_team_id,attendance",
        filters={"attendance": "not.is.null"},
    )
    if not attendance_games:
        return []

    teams = select("teams", columns="id,abbreviation")
    teams_map = {t["id"]: t["abbreviation"] for t in teams}

    att_df = pd.DataFrame(attendance_games)
    att_df["team"] = att_df["home_team_id"].map(teams_map)
    return sorted(att_df["team"].dropna().unique().tolist())
