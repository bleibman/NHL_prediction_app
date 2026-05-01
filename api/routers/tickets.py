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
    TeamPriceTrendPoint,
    PriceAttendancePoint,
    PriceSpreadPoint,
    TicketFilterOptions,
)
from api import cache

router = APIRouter()


def _format_season(s: int) -> str:
    return f"{s // 10000}\u2013{str(s // 10000 + 1)[-2:]}"


def _get_teams_full() -> list[dict]:
    """Return full teams list with division/conference info."""
    cached = cache.get("teams_full")
    if cached is not None:
        return cached
    teams = select("teams", columns="id,abbreviation,name,division,conference")
    cache.set("teams_full", teams, ttl=3600)
    return teams


def _load_venues() -> dict[int, dict]:
    """Load venues table as dict keyed by team_id."""
    cached = cache.get("venues_map")
    if cached is not None:
        return cached
    rows = select("venues", columns="team_id,name,city,state,capacity")
    venues_map = {r["team_id"]: r for r in rows} if rows else {}
    cache.set("venues_map", venues_map, ttl=3600)
    return venues_map


def _load_snapshots():
    cached = cache.get("ticket_snapshots")
    if cached is not None:
        return cached

    snapshots = select(
        "ticket_snapshots",
        columns="seatgeek_event_id,game_date,home_team_id,away_team_id,"
        "snapshot_date,lowest_price,average_price,highest_price,listing_count",
        order="game_date.asc",
    )
    teams_list = select("teams", columns="id,name,abbreviation")
    teams_map = {t["id"]: t["abbreviation"] for t in teams_list}
    result = (snapshots, teams_map)
    cache.set("ticket_snapshots", result)
    return result


def _filter_by_team_context(
    df: pd.DataFrame,
    teams_full: list[dict],
    division: str | None,
    team: str | None,
) -> pd.DataFrame:
    """Filter a DataFrame by division or team abbreviation on home_team_id."""
    if team:
        allowed = {t["id"] for t in teams_full if t.get("abbreviation") == team}
        return df[df["home_team_id"].isin(allowed)]
    if division:
        allowed = {t["id"] for t in teams_full if t.get("division") == division}
        return df[df["home_team_id"].isin(allowed)]
    return df


@router.get("/filter-options", response_model=TicketFilterOptions)
def get_filter_options():
    teams_full = _get_teams_full()
    divisions = sorted(set(t["division"] for t in teams_full if t.get("division")))
    teams = sorted(t["abbreviation"] for t in teams_full if t.get("abbreviation"))
    return TicketFilterOptions(divisions=divisions, teams=teams)


@router.get("/summary", response_model=TicketSummary)
def get_summary(division: str | None = None, team: str | None = None):
    snapshots, _ = _load_snapshots()
    if not snapshots:
        return TicketSummary(
            avg_price=None, lowest_price=None, highest_price=None,
            avg_spread=None, total_listings=None, games_tracked=0,
            snapshot_date=None,
        )

    snap_df = pd.DataFrame(snapshots)
    latest_date = snap_df["snapshot_date"].max()
    latest = snap_df[snap_df["snapshot_date"] == latest_date]

    if division or team:
        teams_full = _get_teams_full()
        latest = _filter_by_team_context(latest, teams_full, division, team)

    if latest.empty:
        return TicketSummary(
            avg_price=None, lowest_price=None, highest_price=None,
            avg_spread=None, total_listings=None, games_tracked=0,
            snapshot_date=str(latest_date),
        )

    avg_ticket = latest["average_price"].mean()
    lowest_avail = latest["lowest_price"].min()
    highest_avail = latest["highest_price"].max()
    total_listings = latest["listing_count"].sum()

    spread = latest["highest_price"] - latest["lowest_price"]
    avg_spread = spread.mean()

    return TicketSummary(
        avg_price=round(float(avg_ticket), 0) if pd.notna(avg_ticket) else None,
        lowest_price=int(lowest_avail) if pd.notna(lowest_avail) else None,
        highest_price=int(highest_avail) if pd.notna(highest_avail) else None,
        avg_spread=round(float(avg_spread), 0) if pd.notna(avg_spread) else None,
        total_listings=int(total_listings) if pd.notna(total_listings) else None,
        games_tracked=len(latest),
        snapshot_date=str(latest_date),
    )


@router.get("/upcoming", response_model=list[UpcomingGame])
def get_upcoming(division: str | None = None, team: str | None = None):
    snapshots, teams_map = _load_snapshots()
    if not snapshots:
        return []

    snap_df = pd.DataFrame(snapshots)
    latest_date = snap_df["snapshot_date"].max()
    latest = snap_df[snap_df["snapshot_date"] == latest_date]

    if division or team:
        teams_full = _get_teams_full()
        latest = _filter_by_team_context(latest, teams_full, division, team)

    venues_map = _load_venues()

    result = []
    for _, row in latest.iterrows():
        game_date = pd.to_datetime(row["game_date"])
        venue = venues_map.get(row["home_team_id"], {})
        low = int(row["lowest_price"]) if pd.notna(row["lowest_price"]) else None
        high = int(row["highest_price"]) if pd.notna(row["highest_price"]) else None
        spread = (high - low) if (low is not None and high is not None) else None
        result.append(UpcomingGame(
            date=game_date.strftime("%b %d, %Y"),
            home_team=teams_map.get(row["home_team_id"], "?"),
            away_team=teams_map.get(row["away_team_id"], "?"),
            avg_price=int(row["average_price"]) if pd.notna(row["average_price"]) else None,
            low_price=low,
            high_price=high,
            listings=int(row["listing_count"]) if pd.notna(row["listing_count"]) else None,
            venue_name=venue.get("name"),
            venue_city=venue.get("city"),
            venue_capacity=venue.get("capacity"),
            spread=spread,
        ))
    result.sort(key=lambda g: g.date)
    return result


@router.get("/price-trends", response_model=list[PriceTrendPoint])
def get_price_trends(division: str | None = None, team: str | None = None):
    snapshots, _ = _load_snapshots()
    if not snapshots:
        return []

    snap_df = pd.DataFrame(snapshots)

    if division or team:
        teams_full = _get_teams_full()
        snap_df = _filter_by_team_context(snap_df, teams_full, division, team)

    if snap_df.empty or snap_df["snapshot_date"].nunique() < 2:
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


@router.get("/price-trends-by-team", response_model=list[TeamPriceTrendPoint])
def get_price_trends_by_team(division: str | None = None, team: str | None = None):
    snapshots, teams_map = _load_snapshots()
    if not snapshots:
        return []

    snap_df = pd.DataFrame(snapshots)

    if division or team:
        teams_full = _get_teams_full()
        snap_df = _filter_by_team_context(snap_df, teams_full, division, team)

    if snap_df.empty or snap_df["snapshot_date"].nunique() < 2:
        return []

    snap_df["game_date"] = pd.to_datetime(snap_df["game_date"])
    snap_df["snapshot_date"] = pd.to_datetime(snap_df["snapshot_date"])
    snap_df["days_until_game"] = (snap_df["game_date"] - snap_df["snapshot_date"]).dt.days
    snap_df = snap_df[snap_df["days_until_game"] >= 0]
    snap_df["team"] = snap_df["home_team_id"].map(teams_map)
    snap_df = snap_df.dropna(subset=["team"])

    if snap_df.empty:
        return []

    grouped = (
        snap_df.groupby(["team", "days_until_game"])["average_price"]
        .mean()
        .reset_index()
        .sort_values(["team", "days_until_game"])
    )
    return [
        TeamPriceTrendPoint(
            team=row["team"],
            days_until_game=int(row["days_until_game"]),
            average_price=round(float(row["average_price"]), 2),
        )
        for _, row in grouped.iterrows()
    ]


@router.get("/team-prices", response_model=list[TeamPrice])
def get_team_prices(division: str | None = None):
    snapshots, teams_map = _load_snapshots()
    if not snapshots:
        return []

    snap_df = pd.DataFrame(snapshots)
    latest_date = snap_df["snapshot_date"].max()
    latest = snap_df[snap_df["snapshot_date"] == latest_date]

    if division:
        teams_full = _get_teams_full()
        latest = _filter_by_team_context(latest, teams_full, division, None)

    team_agg = (
        latest.groupby("home_team_id")
        .agg(
            average_price=("average_price", "mean"),
            lowest_price=("lowest_price", "min"),
            highest_price=("highest_price", "max"),
        )
        .reset_index()
        .sort_values("average_price", ascending=True)
    )
    team_agg["team"] = team_agg["home_team_id"].map(teams_map)
    team_agg["spread"] = team_agg["highest_price"] - team_agg["lowest_price"]
    team_agg = team_agg.dropna(subset=["team", "average_price"])

    return [
        TeamPrice(
            team=row["team"],
            average_price=round(float(row["average_price"]), 2),
            lowest_price=round(float(row["lowest_price"]), 2) if pd.notna(row["lowest_price"]) else None,
            highest_price=round(float(row["highest_price"]), 2) if pd.notna(row["highest_price"]) else None,
            spread=round(float(row["spread"]), 2) if pd.notna(row["spread"]) else None,
        )
        for _, row in team_agg.iterrows()
    ]


@router.get("/spread", response_model=list[PriceSpreadPoint])
def get_spread(division: str | None = None, team: str | None = None):
    snapshots, teams_map = _load_snapshots()
    if not snapshots:
        return []

    snap_df = pd.DataFrame(snapshots)

    if division or team:
        teams_full = _get_teams_full()
        snap_df = _filter_by_team_context(snap_df, teams_full, division, team)

    if snap_df.empty:
        return []

    snap_df["team"] = snap_df["home_team_id"].map(teams_map)
    snap_df = snap_df.dropna(subset=["team"])

    team_spread = (
        snap_df.groupby("team")
        .agg(
            avg_lowest=("lowest_price", "mean"),
            avg_highest=("highest_price", "mean"),
            listing_count=("listing_count", "sum"),
        )
        .reset_index()
    )
    team_spread["avg_spread"] = team_spread["avg_highest"] - team_spread["avg_lowest"]
    team_spread = team_spread.sort_values("avg_spread", ascending=True)

    return [
        PriceSpreadPoint(
            team=row["team"],
            avg_spread=round(float(row["avg_spread"]), 2),
            avg_lowest=round(float(row["avg_lowest"]), 2),
            avg_highest=round(float(row["avg_highest"]), 2),
            listing_count=int(row["listing_count"]),
        )
        for _, row in team_spread.iterrows()
    ]


@router.get("/price-attendance-correlation", response_model=list[PriceAttendancePoint])
def get_price_attendance_correlation():
    snapshots, teams_map = _load_snapshots()
    if not snapshots:
        return []

    snap_df = pd.DataFrame(snapshots)
    snap_df["team"] = snap_df["home_team_id"].map(teams_map)
    snap_df = snap_df.dropna(subset=["team"])

    avg_prices = (
        snap_df.groupby(["home_team_id", "team"])["average_price"]
        .mean()
        .reset_index()
    )

    # Get attendance data
    attendance_games = select(
        "games",
        columns="home_team_id,attendance",
        filters={"attendance": "not.is.null"},
    )
    if not attendance_games:
        return []

    att_df = pd.DataFrame(attendance_games)
    avg_att = (
        att_df.groupby("home_team_id")["attendance"]
        .mean()
        .reset_index()
    )

    venues_map = _load_venues()

    merged = avg_prices.merge(avg_att, on="home_team_id", how="inner")

    result = []
    for _, row in merged.iterrows():
        venue = venues_map.get(row["home_team_id"], {})
        capacity = venue.get("capacity")
        util = round(float(row["attendance"]) / capacity * 100, 1) if capacity else None
        result.append(PriceAttendancePoint(
            team=row["team"],
            avg_ticket_price=round(float(row["average_price"]), 2),
            avg_attendance=round(float(row["attendance"]), 0),
            capacity=capacity,
            utilization_pct=util,
        ))
    return result


@router.get("/attendance", response_model=list[AttendancePoint])
def get_attendance(
    team_abbrev: str | None = None,
    season_id: int | None = None,
    division: str | None = None,
):
    cache_key = f"attendance_{team_abbrev or 'all'}_{season_id or 'all'}_{division or 'all'}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    filters: dict = {"attendance": "not.is.null"}
    if season_id:
        filters["season_id"] = f"eq.{season_id}"

    attendance_games = select(
        "games",
        columns="home_team_id,season_id,attendance",
        filters=filters,
    )
    if not attendance_games:
        return []

    teams = select("teams", columns="id,abbreviation,division")
    teams_map = {t["id"]: t["abbreviation"] for t in teams}
    teams_div = {t["id"]: t.get("division") for t in teams}

    att_df = pd.DataFrame(attendance_games)
    att_df["team"] = att_df["home_team_id"].map(teams_map)

    if team_abbrev:
        att_df = att_df[att_df["team"] == team_abbrev]

    if division:
        att_df["division"] = att_df["home_team_id"].map(teams_div)
        att_df = att_df[att_df["division"] == division]

    if att_df.empty:
        return []

    season_avg = (
        att_df.groupby("season_id")["attendance"]
        .mean()
        .reset_index()
        .sort_values("season_id")
    )
    result = [
        AttendancePoint(
            season_id=int(row["season_id"]),
            season_display=_format_season(int(row["season_id"])),
            avg_attendance=round(float(row["attendance"]), 0),
        )
        for _, row in season_avg.iterrows()
    ]
    cache.set(cache_key, result)
    return result


@router.get("/attendance-teams", response_model=list[str])
def get_attendance_teams():
    cached = cache.get("attendance_teams")
    if cached is not None:
        return cached

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
    result = sorted(att_df["team"].dropna().unique().tolist())
    cache.set("attendance_teams", result)
    return result
