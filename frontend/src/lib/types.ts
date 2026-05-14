export interface DashboardSummary {
  season_id: number;
  season_display: string;
  games_count: number;
  playoff_series_count: number;
  players_count: number;
}

export interface StandingRow {
  team: string;
  gp: number;
  w: number;
  l: number;
  otl: number;
  pts: number;
  pts_pct: number;
  gf: number;
  ga: number;
  pp_pct: number;
  pk_pct: number;
  fo_pct: number;
  sf_pg: number;
  sa_pg: number;
}

export interface ScorerRow {
  player_name: string;
  team: string;
  position: string;
  gp: number;
  goals: number;
  assists: number;
  points: number;
  plus_minus: number | null;
}

export interface PlayoffSeriesRow {
  round_name: string;
  matchup: string;
  score: string;
  winner: string | null;
}

export interface TeamTrendPoint {
  season_id: number;
  season_display: string;
  wins: number;
  losses: number;
  points: number;
  point_pct: number;
  gf_ga_ratio: number;
}

export interface PredictionRow {
  rank: number;
  team_id: number;
  abbreviation: string;
  team_name: string;
  cup_probability: number;
}

export interface TicketSummary {
  avg_price: number | null;
  lowest_price: number | null;
  highest_price: number | null;
  avg_spread: number | null;
  total_listings: number | null;
  games_tracked: number;
  snapshot_date: string | null;
}

export interface UpcomingGame {
  date: string;
  home_team: string;
  away_team: string;
  avg_price: number | null;
  low_price: number | null;
  high_price: number | null;
  listings: number | null;
  venue_name: string | null;
  venue_city: string | null;
  venue_capacity: number | null;
  spread: number | null;
}

export interface PriceTrendPoint {
  days_until_game: number;
  average_price: number;
}

export interface TeamPrice {
  team: string;
  average_price: number;
  lowest_price: number | null;
  highest_price: number | null;
  spread: number | null;
}

export interface AttendancePoint {
  season_id: number;
  season_display: string;
  avg_attendance: number;
}

export interface TeamPriceTrendPoint {
  team: string;
  days_until_game: number;
  average_price: number;
}

export interface PriceAttendancePoint {
  team: string;
  avg_ticket_price: number;
  avg_attendance: number;
  capacity: number | null;
  utilization_pct: number | null;
}

export interface PriceSpreadPoint {
  team: string;
  avg_spread: number;
  avg_lowest: number;
  avg_highest: number;
  listing_count: number;
}

export interface TicketFilterOptions {
  divisions: string[];
  teams: string[];
}

export interface PerformancePricePoint {
  team: string;
  win_pct: number;
  goals_per_game: number;
  shots_per_game: number;
  avg_ticket_price: number;
}

export interface AttendanceOverviewPoint {
  season_id: number;
  season_display: string;
  division: string;
  avg_attendance: number;
  games_count: number;
}

export interface AdvancedAttendancePoint {
  team: string;
  corsi_pct: number;
  x_goals_pct: number;
  fenwick_pct: number;
  avg_attendance: number;
}

export interface TicketsInit {
  summary: TicketSummary;
  upcoming: UpcomingGame[];
  price_trends: PriceTrendPoint[];
  team_trends: TeamPriceTrendPoint[];
  team_prices: TeamPrice[];
  spread: PriceSpreadPoint[];
  correlation: PriceAttendancePoint[];
  attendance_teams: string[];
  filter_options: TicketFilterOptions;
  team_divisions: Record<string, string>;
  performance_price: PerformancePricePoint[];
  attendance_overview: AttendanceOverviewPoint[];
  advanced_attendance: AdvancedAttendancePoint[];
}

export interface SeasonSummaryRow {
  teams_count: number;
  total_games: number;
  avg_goals_per_game: number;
  avg_hits_per_game: number;
  ot_games: number;
}

export interface PhysicalityRow {
  team: string;
  hits_pg: number;
  pim_pg: number;
  blocked_pg: number;
  takeaways_pg: number;
  giveaways_pg: number;
}

export interface SpecialTeamsRow {
  team: string;
  pp_pct: number;
  pk_pct: number;
  pp_opportunities_pg: number;
}

export interface HomeAdvantageRow {
  team: string;
  home_win_pct: number;
  away_win_pct: number;
  differential: number;
}

export interface OvertimeRow {
  team: string;
  ot_so_win_rate: number;
  reg_wins: number;
  ot_wins: number;
  so_wins: number;
  reg_losses: number;
  ot_losses: number;
  so_losses: number;
}

export interface ShotQualityRow {
  team: string;
  hd_shot_share: number;
  hd_goal_share: number;
  x_goals_pct: number;
  corsi_pct: number;
}

export interface DivisionTrendRow {
  season_id: number;
  season_display: string;
  division: string;
  metric_value: number;
}

export interface AnalyticsInit {
  seasons: number[];
  selected_season: number | null;
  season_summary: SeasonSummaryRow | null;
  physicality: PhysicalityRow[];
  special_teams: SpecialTeamsRow[];
  home_advantage: HomeAdvantageRow[];
  overtime: OvertimeRow[];
  shot_quality: ShotQualityRow[];
  division_trends: DivisionTrendRow[];
  filter_options: TicketFilterOptions;
  team_divisions: Record<string, string>;
}

export interface DashboardInit {
  summary: DashboardSummary;
  standings: StandingRow[];
  scorers: ScorerRow[];
  seasons: number[];
  divisions: string[];
  teams: string[];
  team_divisions: Record<string, string>;
}

export interface HistoricalSeasonData {
  standings: StandingRow[];
  scorers: ScorerRow[];
  playoffs: PlayoffSeriesRow[];
}

export interface RefreshEvent {
  step?: number;
  total?: number;
  label?: string;
  status?: "running" | "done" | "error";
  error?: string;
  done?: boolean;
}
