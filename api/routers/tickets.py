"""Ticket analytics API endpoints."""

import asyncio

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
    TicketsInit,
    PerformancePricePoint,
    AttendanceOverviewPoint,
    AdvancedAttendancePoint,
    SeasonSummaryRow,
    PhysicalityRow,
    SpecialTeamsRow,
    HomeAdvantageRow,
    OvertimeRow,
    ShotQualityRow,
    DivisionTrendRow,
    AnalyticsInit,
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


@router.get("/init", response_model=TicketsInit)
async def get_tickets_init():
    cached = cache.get("tickets_init")
    if cached is not None:
        return cached

    (
        summary, upcoming, price_trends, team_trends,
        team_prices, spread, correlation, attendance_teams,
        filter_options, perf_price, att_overview, adv_att,
    ) = await asyncio.gather(
        asyncio.to_thread(get_summary),
        asyncio.to_thread(get_upcoming),
        asyncio.to_thread(get_price_trends),
        asyncio.to_thread(get_price_trends_by_team),
        asyncio.to_thread(get_team_prices),
        asyncio.to_thread(get_spread),
        asyncio.to_thread(get_price_attendance_correlation),
        asyncio.to_thread(get_attendance_teams),
        asyncio.to_thread(get_filter_options),
        asyncio.to_thread(get_performance_price),
        asyncio.to_thread(get_attendance_overview),
        asyncio.to_thread(get_advanced_attendance),
    )

    teams_full = _get_teams_full()  # already cached by get_filter_options()
    team_divisions = {
        t["abbreviation"]: t["division"]
        for t in teams_full
        if t.get("abbreviation") and t.get("division")
    }

    result = TicketsInit(
        summary=summary,
        upcoming=upcoming,
        price_trends=price_trends,
        team_trends=team_trends,
        team_prices=team_prices,
        spread=spread,
        correlation=correlation,
        attendance_teams=attendance_teams,
        filter_options=filter_options,
        team_divisions=team_divisions,
        performance_price=perf_price,
        attendance_overview=att_overview,
        advanced_attendance=adv_att,
    )
    cache.set("tickets_init", result, ttl=900)
    return result


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

    snap_df = snap_df.dropna(subset=["average_price"])
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

    snap_df = snap_df.dropna(subset=["average_price"])
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
    team_spread = team_spread.dropna(subset=["avg_lowest", "avg_highest", "avg_spread"])
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
    snap_df = snap_df.dropna(subset=["team", "average_price"])

    if snap_df.empty:
        return []

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
    merged = merged.dropna(subset=["average_price", "attendance"])

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


@router.get("/performance-price", response_model=list[PerformancePricePoint])
def get_performance_price():
    cached = cache.get("performance_price")
    if cached is not None:
        return cached

    try:
        stats = select("game_team_stats", columns="team_id,won,goals,shots")
    except Exception:
        return []
    if not stats:
        return []

    teams_list = select("teams", columns="id,abbreviation")
    teams_map = {t["id"]: t["abbreviation"] for t in teams_list}

    df = pd.DataFrame(stats)
    df = df.dropna(subset=["won", "goals", "shots"])
    if df.empty:
        return []

    agg = (
        df.groupby("team_id")
        .agg(
            total_games=("won", "count"),
            wins=("won", "sum"),
            avg_goals=("goals", "mean"),
            avg_shots=("shots", "mean"),
        )
        .reset_index()
    )
    agg = agg[agg["total_games"] > 0]
    agg["win_pct"] = agg["wins"] / agg["total_games"]
    agg["team"] = agg["team_id"].map(teams_map)
    agg = agg.dropna(subset=["team", "win_pct", "avg_goals", "avg_shots"])

    # Get avg ticket prices per team
    snapshots, snap_teams_map = _load_snapshots()
    if not snapshots:
        return []

    snap_df = pd.DataFrame(snapshots)
    snap_df["team"] = snap_df["home_team_id"].map(snap_teams_map)
    snap_df = snap_df.dropna(subset=["team", "average_price"])
    avg_prices = (
        snap_df.groupby("team")["average_price"]
        .mean()
        .reset_index()
        .rename(columns={"average_price": "avg_ticket_price"})
    )

    merged = agg.merge(avg_prices, on="team", how="inner")
    merged = merged.dropna(subset=["avg_ticket_price"])

    result = [
        PerformancePricePoint(
            team=row["team"],
            win_pct=round(float(row["win_pct"]), 3),
            goals_per_game=round(float(row["avg_goals"]), 2),
            shots_per_game=round(float(row["avg_shots"]), 1),
            avg_ticket_price=round(float(row["avg_ticket_price"]), 2),
        )
        for _, row in merged.iterrows()
    ]
    cache.set("performance_price", result)
    return result


@router.get("/attendance-overview", response_model=list[AttendanceOverviewPoint])
def get_attendance_overview():
    cached = cache.get("attendance_overview")
    if cached is not None:
        return cached

    games = select(
        "games",
        columns="home_team_id,season_id,attendance",
        filters={"attendance": "not.is.null"},
    )
    if not games:
        return []

    teams_full = _get_teams_full()
    team_div = {t["id"]: t.get("division") for t in teams_full}

    df = pd.DataFrame(games)
    df["division"] = df["home_team_id"].map(team_div)
    df = df.dropna(subset=["division"])

    grouped = (
        df.groupby(["season_id", "division"])
        .agg(
            avg_attendance=("attendance", "mean"),
            games_count=("attendance", "count"),
        )
        .reset_index()
        .sort_values("season_id")
    )

    result = [
        AttendanceOverviewPoint(
            season_id=int(row["season_id"]),
            season_display=_format_season(int(row["season_id"])),
            division=row["division"],
            avg_attendance=round(float(row["avg_attendance"]), 0),
            games_count=int(row["games_count"]),
        )
        for _, row in grouped.iterrows()
    ]
    cache.set("attendance_overview", result)
    return result


@router.get("/advanced-attendance", response_model=list[AdvancedAttendancePoint])
def get_advanced_attendance():
    cached = cache.get("advanced_attendance")
    if cached is not None:
        return cached

    try:
        adv_stats = select(
            "game_advanced_stats",
            columns="game_id,team_id,corsi_pct,x_goals_pct,fenwick_pct",
            filters={"situation": "eq.all"},
        )
    except Exception:
        return []
    if not adv_stats:
        return []

    att_games = select(
        "games",
        columns="id,home_team_id,attendance",
        filters={"attendance": "not.is.null"},
    )
    if not att_games:
        return []

    teams_list = select("teams", columns="id,abbreviation")
    teams_map = {t["id"]: t["abbreviation"] for t in teams_list}

    adv_df = pd.DataFrame(adv_stats)
    games_df = pd.DataFrame(att_games).rename(columns={"id": "game_id"})

    # Join on game_id, keep only home team rows to avoid double-counting attendance
    merged = adv_df.merge(games_df, on="game_id", how="inner")
    merged = merged[merged["team_id"] == merged["home_team_id"]]

    if merged.empty:
        return []

    merged["team"] = merged["team_id"].map(teams_map)
    merged = merged.dropna(subset=["team", "corsi_pct", "x_goals_pct", "fenwick_pct"])

    grouped = (
        merged.groupby("team")
        .agg(
            corsi_pct=("corsi_pct", "mean"),
            x_goals_pct=("x_goals_pct", "mean"),
            fenwick_pct=("fenwick_pct", "mean"),
            avg_attendance=("attendance", "mean"),
        )
        .reset_index()
    )

    result = [
        AdvancedAttendancePoint(
            team=row["team"],
            corsi_pct=round(float(row["corsi_pct"]) * 100, 1),
            x_goals_pct=round(float(row["x_goals_pct"]) * 100, 1),
            fenwick_pct=round(float(row["fenwick_pct"]) * 100, 1),
            avg_attendance=round(float(row["avg_attendance"]), 0),
        )
        for _, row in grouped.iterrows()
    ]
    cache.set("advanced_attendance", result)
    return result


# ── Team Analytics endpoints ──


def _game_ids_for_season(season_id: int) -> list[int]:
    """Return game IDs for a season. Cached 1hr."""
    cache_key = f"game_ids_{season_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    games = select("games", columns="id", filters={"season_id": f"eq.{season_id}"})
    ids = [g["id"] for g in games] if games else []
    cache.set(cache_key, ids, ttl=3600)
    return ids


def _select_by_game_ids(
    table: str, columns: str, game_ids: list[int],
    extra_filters: dict | None = None, batch_size: int = 50,
) -> list[dict]:
    """Query a table filtered by game_id using batched in.() calls."""
    all_rows: list[dict] = []
    for i in range(0, len(game_ids), batch_size):
        batch = game_ids[i : i + batch_size]
        id_str = ",".join(str(gid) for gid in batch)
        filters = {"game_id": f"in.({id_str})"}
        if extra_filters:
            filters.update(extra_filters)
        rows = select(table, columns=columns, filters=filters)
        if rows:
            all_rows.extend(rows)
    return all_rows


def _load_game_team_stats_for_season(season_id: int) -> pd.DataFrame:
    """Load game_team_stats for a single season using batched in.() queries."""
    cache_key = f"gts_season_{season_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    game_ids = _game_ids_for_season(season_id)
    if not game_ids:
        return pd.DataFrame()

    stats = _select_by_game_ids(
        "game_team_stats",
        "game_id,team_id,is_home,won,settled_in,goals,shots,hits,pim,"
        "power_play_opportunities,power_play_goals,faceoff_win_pct,"
        "giveaways,takeaways,blocked",
        game_ids,
    )
    df = pd.DataFrame(stats) if stats else pd.DataFrame()
    cache.set(cache_key, df, ttl=3600)
    return df


def _load_advanced_stats_for_season(season_id: int) -> pd.DataFrame:
    """Load game_advanced_stats (situation=all) for a single season."""
    cache_key = f"adv_season_{season_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    game_ids = _game_ids_for_season(season_id)
    if not game_ids:
        return pd.DataFrame()

    try:
        rows = _select_by_game_ids(
            "game_advanced_stats",
            "game_id,team_id,corsi_pct,x_goals_pct,"
            "high_danger_shots_for,high_danger_shots_against,"
            "high_danger_goals_for,high_danger_goals_against",
            game_ids,
            extra_filters={"situation": "eq.all"},
        )
    except Exception:
        rows = []

    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    cache.set(cache_key, df, ttl=3600)
    return df


def _get_available_seasons() -> list[int]:
    """Return season IDs that have game_team_stats data.

    Uses season_stats table (small, ~640 rows) as a proxy rather than
    scanning the full games + game_team_stats tables.
    """
    cached = cache.get("analytics_seasons")
    if cached is not None:
        return cached

    rows = select("season_stats", columns="season_id")
    if not rows:
        return []

    seasons = sorted(set(r["season_id"] for r in rows), reverse=True)
    cache.set("analytics_seasons", seasons, ttl=3600)
    return seasons


@router.get("/season-summary", response_model=SeasonSummaryRow | None)
def get_season_summary(season_id: int):
    cache_key = f"season_summary_{season_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    df = _load_game_team_stats_for_season(season_id)
    if df.empty:
        return None

    teams_count = df["team_id"].nunique()
    total_games = df["game_id"].nunique()
    avg_goals = df["goals"].mean()
    avg_hits = df["hits"].mean() if "hits" in df.columns and df["hits"].notna().any() else 0
    ot_games = df[df["settled_in"].isin(["OT", "SO"])]["game_id"].nunique() if "settled_in" in df.columns else 0

    result = SeasonSummaryRow(
        teams_count=int(teams_count),
        total_games=int(total_games),
        avg_goals_per_game=round(float(avg_goals), 2),
        avg_hits_per_game=round(float(avg_hits), 1),
        ot_games=int(ot_games),
    )
    cache.set(cache_key, result, ttl=3600)
    return result


@router.get("/physicality", response_model=list[PhysicalityRow])
def get_physicality(season_id: int):
    cache_key = f"physicality_{season_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    df = _load_game_team_stats_for_season(season_id)
    if df.empty:
        return []

    teams_map = {t["id"]: t["abbreviation"] for t in _get_teams_full()}

    agg = (
        df.groupby("team_id")
        .agg(
            games=("game_id", "count"),
            hits=("hits", "sum"),
            pim=("pim", "sum"),
            blocked=("blocked", "sum"),
            takeaways=("takeaways", "sum"),
            giveaways=("giveaways", "sum"),
        )
        .reset_index()
    )
    agg = agg[agg["games"] > 0]
    agg["team"] = agg["team_id"].map(teams_map)
    agg = agg.dropna(subset=["team"])

    result = sorted(
        [
            PhysicalityRow(
                team=row["team"],
                hits_pg=round(float(row["hits"]) / row["games"], 1),
                pim_pg=round(float(row["pim"]) / row["games"], 1),
                blocked_pg=round(float(row["blocked"]) / row["games"], 1),
                takeaways_pg=round(float(row["takeaways"]) / row["games"], 1),
                giveaways_pg=round(float(row["giveaways"]) / row["games"], 1),
            )
            for _, row in agg.iterrows()
        ],
        key=lambda r: r.hits_pg,
        reverse=True,
    )
    cache.set(cache_key, result, ttl=3600)
    return result


@router.get("/special-teams", response_model=list[SpecialTeamsRow])
def get_special_teams(season_id: int):
    cache_key = f"special_teams_{season_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Try season_stats first for PP% and PK%
    season_stats = select(
        "season_stats",
        columns="team_id,pp_pct,pk_pct",
        filters={"season_id": f"eq.{season_id}"},
    )

    df = _load_game_team_stats_for_season(season_id)
    if df.empty and not season_stats:
        return []

    teams_map = {t["id"]: t["abbreviation"] for t in _get_teams_full()}

    # Get PP opportunities per game from game_team_stats
    pp_opps = pd.DataFrame()
    if not df.empty:
        pp_opps = (
            df.groupby("team_id")
            .agg(
                games=("game_id", "count"),
                pp_opportunities=("power_play_opportunities", "sum"),
                pp_goals=("power_play_goals", "sum"),
            )
            .reset_index()
        )
        pp_opps = pp_opps[pp_opps["games"] > 0]
        pp_opps["pp_opps_pg"] = pp_opps["pp_opportunities"] / pp_opps["games"]

    if season_stats:
        ss_df = pd.DataFrame(season_stats)
        ss_df["team"] = ss_df["team_id"].map(teams_map)
        ss_df = ss_df.dropna(subset=["team", "pp_pct", "pk_pct"])

        if not pp_opps.empty:
            ss_df = ss_df.merge(
                pp_opps[["team_id", "pp_opps_pg"]],
                on="team_id",
                how="left",
            )
            ss_df["pp_opps_pg"] = ss_df["pp_opps_pg"].fillna(3.0)
        else:
            ss_df["pp_opps_pg"] = 3.0

        result = [
            SpecialTeamsRow(
                team=row["team"],
                pp_pct=round(float(row["pp_pct"]) * 100, 1),
                pk_pct=round(float(row["pk_pct"]) * 100, 1),
                pp_opportunities_pg=round(float(row["pp_opps_pg"]), 2),
            )
            for _, row in ss_df.iterrows()
        ]
    elif not pp_opps.empty:
        # Fallback: compute PP% from game_team_stats
        pp_opps["team"] = pp_opps["team_id"].map(teams_map)
        pp_opps = pp_opps.dropna(subset=["team"])
        pp_opps["pp_pct"] = (
            pp_opps["pp_goals"] / pp_opps["pp_opportunities"].replace(0, 1) * 100
        )
        result = [
            SpecialTeamsRow(
                team=row["team"],
                pp_pct=round(float(row["pp_pct"]), 1),
                pk_pct=0.0,
                pp_opportunities_pg=round(float(row["pp_opps_pg"]), 2),
            )
            for _, row in pp_opps.iterrows()
        ]
    else:
        return []

    cache.set(cache_key, result, ttl=3600)
    return result


@router.get("/home-advantage", response_model=list[HomeAdvantageRow])
def get_home_advantage(season_id: int):
    cache_key = f"home_advantage_{season_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    df = _load_game_team_stats_for_season(season_id)
    if df.empty:
        return []

    teams_map = {t["id"]: t["abbreviation"] for t in _get_teams_full()}

    home = df[df["is_home"] == True]  # noqa: E712
    away = df[df["is_home"] == False]  # noqa: E712

    home_agg = (
        home.groupby("team_id")
        .agg(home_games=("won", "count"), home_wins=("won", "sum"))
        .reset_index()
    )
    away_agg = (
        away.groupby("team_id")
        .agg(away_games=("won", "count"), away_wins=("won", "sum"))
        .reset_index()
    )

    merged = home_agg.merge(away_agg, on="team_id", how="outer").fillna(0)
    merged = merged[(merged["home_games"] > 0) & (merged["away_games"] > 0)]
    merged["home_win_pct"] = merged["home_wins"] / merged["home_games"]
    merged["away_win_pct"] = merged["away_wins"] / merged["away_games"]
    merged["differential"] = merged["home_win_pct"] - merged["away_win_pct"]
    merged["team"] = merged["team_id"].map(teams_map)
    merged = merged.dropna(subset=["team"])
    merged = merged.sort_values("differential", ascending=False)

    result = [
        HomeAdvantageRow(
            team=row["team"],
            home_win_pct=round(float(row["home_win_pct"]) * 100, 1),
            away_win_pct=round(float(row["away_win_pct"]) * 100, 1),
            differential=round(float(row["differential"]) * 100, 1),
        )
        for _, row in merged.iterrows()
    ]
    cache.set(cache_key, result, ttl=3600)
    return result


@router.get("/overtime", response_model=list[OvertimeRow])
def get_overtime(season_id: int):
    cache_key = f"overtime_{season_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    df = _load_game_team_stats_for_season(season_id)
    if df.empty or "settled_in" not in df.columns:
        return []

    teams_map = {t["id"]: t["abbreviation"] for t in _get_teams_full()}

    df = df.dropna(subset=["settled_in", "won"])

    result = []
    for team_id, grp in df.groupby("team_id"):
        team = teams_map.get(team_id)
        if not team:
            continue

        reg = grp[grp["settled_in"] == "REG"]
        ot = grp[grp["settled_in"] == "OT"]
        so = grp[grp["settled_in"] == "SO"]

        reg_wins = int(reg["won"].sum())
        ot_wins = int(ot["won"].sum())
        so_wins = int(so["won"].sum())
        reg_losses = int(len(reg) - reg_wins)
        ot_losses = int(len(ot) - ot_wins)
        so_losses = int(len(so) - so_wins)

        ot_so_total = len(ot) + len(so)
        ot_so_win_rate = (ot_wins + so_wins) / ot_so_total * 100 if ot_so_total > 0 else 0

        result.append(
            OvertimeRow(
                team=team,
                ot_so_win_rate=round(ot_so_win_rate, 1),
                reg_wins=reg_wins,
                ot_wins=ot_wins,
                so_wins=so_wins,
                reg_losses=reg_losses,
                ot_losses=ot_losses,
                so_losses=so_losses,
            )
        )

    result.sort(key=lambda r: r.ot_so_win_rate, reverse=True)
    cache.set(cache_key, result, ttl=3600)
    return result


@router.get("/shot-quality", response_model=list[ShotQualityRow])
def get_shot_quality(season_id: int):
    cache_key = f"shot_quality_{season_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    df = _load_advanced_stats_for_season(season_id)
    if df.empty:
        return []

    teams_map = {t["id"]: t["abbreviation"] for t in _get_teams_full()}

    agg = (
        df.groupby("team_id")
        .agg(
            corsi_pct=("corsi_pct", "mean"),
            x_goals_pct=("x_goals_pct", "mean"),
            hd_shots_for=("high_danger_shots_for", "sum"),
            hd_shots_against=("high_danger_shots_against", "sum"),
            hd_goals_for=("high_danger_goals_for", "sum"),
            hd_goals_against=("high_danger_goals_against", "sum"),
        )
        .reset_index()
    )

    total_hd_shots = agg["hd_shots_for"] + agg["hd_shots_against"]
    total_hd_goals = agg["hd_goals_for"] + agg["hd_goals_against"]
    agg["hd_shot_share"] = (agg["hd_shots_for"] / total_hd_shots.replace(0, 1)) * 100
    agg["hd_goal_share"] = (agg["hd_goals_for"] / total_hd_goals.replace(0, 1)) * 100
    agg["team"] = agg["team_id"].map(teams_map)
    agg = agg.dropna(subset=["team"])

    result = [
        ShotQualityRow(
            team=row["team"],
            hd_shot_share=round(float(row["hd_shot_share"]), 1),
            hd_goal_share=round(float(row["hd_goal_share"]), 1),
            x_goals_pct=round(float(row["x_goals_pct"]) * 100, 1),
            corsi_pct=round(float(row["corsi_pct"]) * 100, 1),
        )
        for _, row in agg.iterrows()
    ]
    cache.set(cache_key, result, ttl=3600)
    return result


@router.get("/division-trends", response_model=list[DivisionTrendRow])
def get_division_trends(metric: str = "points"):
    cache_key = f"division_trends_{metric}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    col_map = {
        "points": "points",
        "gf_pg": "goals_for_pg",
        "ga_pg": "goals_against_pg",
        "pp_pct": "pp_pct",
        "pk_pct": "pk_pct",
    }
    db_col = col_map.get(metric, "points")

    stats = select(
        "season_stats",
        columns=f"season_id,team_id,{db_col}",
    )
    if not stats:
        return []

    teams_full = _get_teams_full()
    team_div = {t["id"]: t.get("division") for t in teams_full}

    df = pd.DataFrame(stats)
    df["division"] = df["team_id"].map(team_div)
    df = df.dropna(subset=["division", db_col])

    grouped = (
        df.groupby(["season_id", "division"])[db_col]
        .mean()
        .reset_index()
        .sort_values("season_id")
    )

    result = [
        DivisionTrendRow(
            season_id=int(row["season_id"]),
            season_display=_format_season(int(row["season_id"])),
            division=row["division"],
            metric_value=round(float(row[db_col]), 2),
        )
        for _, row in grouped.iterrows()
    ]
    cache.set(cache_key, result, ttl=3600)
    return result


@router.get("/analytics-init", response_model=AnalyticsInit)
async def get_analytics_init(season_id: int | None = None):
    seasons = _get_available_seasons()
    if not season_id and seasons:
        season_id = seasons[0]
    elif not seasons:
        fo = get_filter_options()
        teams_full = _get_teams_full()
        team_divisions = {
            t["abbreviation"]: t["division"]
            for t in teams_full
            if t.get("abbreviation") and t.get("division")
        }
        return AnalyticsInit(
            seasons=[],
            season_summary=None,
            physicality=[],
            special_teams=[],
            home_advantage=[],
            overtime=[],
            shot_quality=[],
            division_trends=[],
            filter_options=fo,
            team_divisions=team_divisions,
        )

    # Pre-warm per-season caches so parallel threads don't duplicate queries
    await asyncio.to_thread(_game_ids_for_season, season_id)
    await asyncio.gather(
        asyncio.to_thread(_load_game_team_stats_for_season, season_id),
        asyncio.to_thread(_load_advanced_stats_for_season, season_id),
    )

    (
        summary, physicality, special_teams,
        home_advantage, overtime, shot_quality,
        division_trends, fo,
    ) = await asyncio.gather(
        asyncio.to_thread(get_season_summary, season_id),
        asyncio.to_thread(get_physicality, season_id),
        asyncio.to_thread(get_special_teams, season_id),
        asyncio.to_thread(get_home_advantage, season_id),
        asyncio.to_thread(get_overtime, season_id),
        asyncio.to_thread(get_shot_quality, season_id),
        asyncio.to_thread(get_division_trends),
        asyncio.to_thread(get_filter_options),
    )

    teams_full = _get_teams_full()
    team_divisions = {
        t["abbreviation"]: t["division"]
        for t in teams_full
        if t.get("abbreviation") and t.get("division")
    }

    return AnalyticsInit(
        seasons=seasons,
        season_summary=summary,
        physicality=physicality,
        special_teams=special_teams,
        home_advantage=home_advantage,
        overtime=overtime,
        shot_quality=shot_quality,
        division_trends=division_trends,
        filter_options=fo,
        team_divisions=team_divisions,
    )
