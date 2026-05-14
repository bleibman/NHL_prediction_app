"""Pydantic response models for the NHL Predictions API."""

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    season_id: int
    season_display: str
    games_count: int
    playoff_series_count: int
    players_count: int


class StandingRow(BaseModel):
    team: str
    gp: int
    w: int
    l: int
    otl: int
    pts: int
    pts_pct: float
    gf: int
    ga: int
    pp_pct: float
    pk_pct: float
    fo_pct: float
    sf_pg: float
    sa_pg: float


class ScorerRow(BaseModel):
    player_name: str
    team: str
    position: str
    gp: int
    goals: int
    assists: int
    points: int
    plus_minus: int | None = None


class PlayoffSeriesRow(BaseModel):
    round_name: str
    matchup: str
    score: str
    winner: str | None


class TeamTrendPoint(BaseModel):
    season_id: int
    season_display: str
    wins: int
    losses: int
    points: int
    point_pct: float
    gf_ga_ratio: float


class PredictionRequest(BaseModel):
    season_id: int


class PredictionRow(BaseModel):
    rank: int
    team_id: int
    abbreviation: str
    team_name: str
    cup_probability: float


class TicketSummary(BaseModel):
    avg_price: float | None
    lowest_price: int | None
    highest_price: int | None = None
    avg_spread: float | None = None
    total_listings: int | None
    games_tracked: int
    snapshot_date: str | None


class UpcomingGame(BaseModel):
    date: str
    home_team: str
    away_team: str
    avg_price: int | None
    low_price: int | None
    high_price: int | None
    listings: int | None
    venue_name: str | None = None
    venue_city: str | None = None
    venue_capacity: int | None = None
    spread: int | None = None


class PriceTrendPoint(BaseModel):
    days_until_game: int
    average_price: float


class TeamPrice(BaseModel):
    team: str
    average_price: float
    lowest_price: float | None = None
    highest_price: float | None = None
    spread: float | None = None


class AttendancePoint(BaseModel):
    season_id: int
    season_display: str
    avg_attendance: float


class TeamPriceTrendPoint(BaseModel):
    team: str
    days_until_game: int
    average_price: float


class PriceAttendancePoint(BaseModel):
    team: str
    avg_ticket_price: float
    avg_attendance: float
    capacity: int | None
    utilization_pct: float | None


class PriceSpreadPoint(BaseModel):
    team: str
    avg_spread: float
    avg_lowest: float
    avg_highest: float
    listing_count: int


class TicketFilterOptions(BaseModel):
    divisions: list[str]
    teams: list[str]


class PerformancePricePoint(BaseModel):
    team: str
    win_pct: float
    goals_per_game: float
    shots_per_game: float
    avg_ticket_price: float


class AttendanceOverviewPoint(BaseModel):
    season_id: int
    season_display: str
    division: str
    avg_attendance: float
    games_count: int


class AdvancedAttendancePoint(BaseModel):
    team: str
    corsi_pct: float
    x_goals_pct: float
    fenwick_pct: float
    avg_attendance: float


class TicketsInit(BaseModel):
    summary: TicketSummary
    upcoming: list[UpcomingGame]
    price_trends: list[PriceTrendPoint]
    team_trends: list[TeamPriceTrendPoint]
    team_prices: list[TeamPrice]
    spread: list[PriceSpreadPoint]
    correlation: list[PriceAttendancePoint]
    attendance_teams: list[str]
    filter_options: TicketFilterOptions
    team_divisions: dict[str, str]
    performance_price: list[PerformancePricePoint]
    attendance_overview: list[AttendanceOverviewPoint]
    advanced_attendance: list[AdvancedAttendancePoint]


class SeasonSummaryRow(BaseModel):
    teams_count: int
    total_games: int
    avg_goals_per_game: float
    avg_hits_per_game: float
    ot_games: int


class PhysicalityRow(BaseModel):
    team: str
    hits_pg: float
    pim_pg: float
    blocked_pg: float
    takeaways_pg: float
    giveaways_pg: float


class SpecialTeamsRow(BaseModel):
    team: str
    pp_pct: float
    pk_pct: float
    pp_opportunities_pg: float


class HomeAdvantageRow(BaseModel):
    team: str
    home_win_pct: float
    away_win_pct: float
    differential: float


class OvertimeRow(BaseModel):
    team: str
    ot_so_win_rate: float
    reg_wins: int
    ot_wins: int
    so_wins: int
    reg_losses: int
    ot_losses: int
    so_losses: int


class ShotQualityRow(BaseModel):
    team: str
    hd_shot_share: float
    hd_goal_share: float
    x_goals_pct: float
    corsi_pct: float


class DivisionTrendRow(BaseModel):
    season_id: int
    season_display: str
    division: str
    metric_value: float


class AnalyticsInit(BaseModel):
    seasons: list[int]
    selected_season: int | None = None
    season_summary: SeasonSummaryRow | None
    physicality: list[PhysicalityRow]
    special_teams: list[SpecialTeamsRow]
    home_advantage: list[HomeAdvantageRow]
    overtime: list[OvertimeRow]
    shot_quality: list[ShotQualityRow]
    division_trends: list[DivisionTrendRow]
    filter_options: TicketFilterOptions
    team_divisions: dict[str, str]


class DashboardInit(BaseModel):
    summary: DashboardSummary
    standings: list[StandingRow]
    scorers: list[ScorerRow]
    seasons: list[int]
    divisions: list[str]
    teams: list[str]
    team_divisions: dict[str, str]


class HistoricalSeasonData(BaseModel):
    standings: list[StandingRow]
    scorers: list[ScorerRow]
    playoffs: list[PlayoffSeriesRow]


class RefreshRequest(BaseModel):
    season_id: int | None = None
