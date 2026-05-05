-- NHL Prediction App — Supabase Schema (public)
-- Run this in the Supabase SQL Editor (Dashboard > SQL Editor)

-- ============================================================
-- teams
-- ============================================================
CREATE TABLE IF NOT EXISTS teams (
    id           integer PRIMARY KEY,            -- NHL team ID
    abbreviation text NOT NULL,                   -- e.g. "NYR"
    name         text NOT NULL,                   -- "New York Rangers"
    division     text,
    conference   text
);

ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to teams" ON teams;
CREATE POLICY "Allow all access to teams"
    ON teams FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON teams TO anon, authenticated, service_role;

-- ============================================================
-- season_stats
-- ============================================================
CREATE TABLE IF NOT EXISTS season_stats (
    id                serial PRIMARY KEY,
    season_id         integer NOT NULL,
    team_id           integer NOT NULL REFERENCES teams(id),
    games_played      integer,
    wins              integer,
    losses            integer,
    ot_losses         integer,
    points            integer,
    point_pct         real,
    goals_for         integer,
    goals_against     integer,
    goals_for_pg      real,
    goals_against_pg  real,
    pp_pct            real,
    pk_pct            real,
    shots_for_pg      real,
    shots_against_pg  real,
    faceoff_pct       real,
    regulation_wins   integer,
    shootout_wins     integer,
    UNIQUE (season_id, team_id)
);

ALTER TABLE season_stats ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to season_stats" ON season_stats;
CREATE POLICY "Allow all access to season_stats"
    ON season_stats FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON season_stats TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE season_stats_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- games
-- ============================================================
CREATE TABLE IF NOT EXISTS games (
    id              integer PRIMARY KEY,          -- NHL game ID
    season_id       integer NOT NULL,
    game_type       integer,                      -- 2 = regular, 3 = playoff
    game_date       date,
    home_team_id    integer REFERENCES teams(id),
    away_team_id    integer REFERENCES teams(id),
    home_score      integer,
    away_score      integer,
    overtime        boolean DEFAULT false,
    shootout        boolean DEFAULT false
);

ALTER TABLE games ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to games" ON games;
CREATE POLICY "Allow all access to games"
    ON games FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON games TO anon, authenticated, service_role;

-- ============================================================
-- playoff_series
-- ============================================================
CREATE TABLE IF NOT EXISTS playoff_series (
    id               serial PRIMARY KEY,
    season_id        integer NOT NULL,
    round            integer NOT NULL,             -- 1-4
    series_letter    text,                         -- A-O
    top_seed_id      integer REFERENCES teams(id),
    bottom_seed_id   integer REFERENCES teams(id),
    top_seed_wins    integer DEFAULT 0,
    bottom_seed_wins integer DEFAULT 0,
    winning_team_id  integer REFERENCES teams(id),
    losing_team_id   integer REFERENCES teams(id),
    UNIQUE (season_id, series_letter)
);

ALTER TABLE playoff_series ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to playoff_series" ON playoff_series;
CREATE POLICY "Allow all access to playoff_series"
    ON playoff_series FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON playoff_series TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE playoff_series_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- player_stats
-- ============================================================
CREATE TABLE IF NOT EXISTS player_stats (
    id                 serial PRIMARY KEY,
    player_id          integer NOT NULL,            -- NHL player ID
    player_name        text,
    season_id          integer NOT NULL,
    team_id            integer REFERENCES teams(id),
    team_abbrev        text,                        -- raw from API
    position           text,                        -- C, L, R, D
    games_played       integer,
    goals              integer,
    assists            integer,
    points             integer,
    plus_minus         integer,
    pim                integer,
    ev_goals           integer,
    ev_points          integer,
    pp_goals           integer,
    pp_points          integer,
    sh_goals           integer,
    sh_points          integer,
    game_winning_goals integer,
    shots              integer,
    shooting_pct       real,
    toi_per_game       real,                        -- seconds
    UNIQUE (player_id, season_id, team_abbrev)
);

ALTER TABLE player_stats ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to player_stats" ON player_stats;
CREATE POLICY "Allow all access to player_stats"
    ON player_stats FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON player_stats TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE player_stats_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- venues
-- ============================================================
CREATE TABLE IF NOT EXISTS venues (
    id              serial PRIMARY KEY,
    team_id         integer NOT NULL REFERENCES teams(id),
    name            text,
    city            text,
    state           text,
    capacity        integer,
    UNIQUE (team_id)
);

ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to venues" ON venues;
CREATE POLICY "Allow all access to venues"
    ON venues FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON venues TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE venues_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- ticket_snapshots
-- ============================================================
CREATE TABLE IF NOT EXISTS ticket_snapshots (
    id                  serial PRIMARY KEY,
    seatgeek_event_id   integer NOT NULL,
    game_date           date,
    home_team_id        integer REFERENCES teams(id),
    away_team_id        integer REFERENCES teams(id),
    snapshot_date       date NOT NULL,
    lowest_price        integer,
    average_price       integer,
    highest_price       integer,
    listing_count       integer,
    UNIQUE (seatgeek_event_id, snapshot_date)
);

ALTER TABLE ticket_snapshots ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to ticket_snapshots" ON ticket_snapshots;
CREATE POLICY "Allow all access to ticket_snapshots"
    ON ticket_snapshots FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON ticket_snapshots TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE ticket_snapshots_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- Add attendance column to games
-- ============================================================
ALTER TABLE games ADD COLUMN IF NOT EXISTS attendance integer;

-- ============================================================
-- Indexes for query performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_season_stats_season_id ON season_stats(season_id);
CREATE INDEX IF NOT EXISTS idx_season_stats_team_id ON season_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_season_stats_points ON season_stats(season_id, points DESC);
CREATE INDEX IF NOT EXISTS idx_games_season_id ON games(season_id);
CREATE INDEX IF NOT EXISTS idx_games_home_team ON games(home_team_id);
CREATE INDEX IF NOT EXISTS idx_games_attendance ON games(home_team_id, season_id) WHERE attendance IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_player_stats_season_id ON player_stats(season_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_points ON player_stats(season_id, points DESC);
CREATE INDEX IF NOT EXISTS idx_playoff_series_season_id ON playoff_series(season_id);
CREATE INDEX IF NOT EXISTS idx_ticket_snapshots_date ON ticket_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_ticket_snapshots_home ON ticket_snapshots(home_team_id);
CREATE INDEX IF NOT EXISTS idx_ticket_snapshots_date_home ON ticket_snapshots(snapshot_date, home_team_id);
CREATE INDEX IF NOT EXISTS idx_ticket_snapshots_game_date ON ticket_snapshots(game_date);
CREATE INDEX IF NOT EXISTS idx_ticket_snapshots_away ON ticket_snapshots(away_team_id);

-- ============================================================
-- RPC: Dashboard summary in one call
-- ============================================================
CREATE OR REPLACE FUNCTION get_dashboard_summary()
RETURNS json
LANGUAGE sql
STABLE
AS $$
  WITH latest AS (
    SELECT season_id FROM season_stats ORDER BY season_id DESC LIMIT 1
  )
  SELECT json_build_object(
    'season_id', l.season_id,
    'games_count', (SELECT count(*) FROM games WHERE season_id = l.season_id),
    'playoff_series_count', (SELECT count(*) FROM playoff_series WHERE season_id = l.season_id),
    'players_count', (SELECT count(*) FROM player_stats WHERE season_id = l.season_id)
  )
  FROM latest l;
$$;

-- ============================================================
-- game_team_stats — per-game per-team box score (Kaggle imports)
-- ============================================================
CREATE TABLE IF NOT EXISTS game_team_stats (
    id                      serial PRIMARY KEY,
    game_id                 integer NOT NULL REFERENCES games(id),
    team_id                 integer NOT NULL REFERENCES teams(id),
    is_home                 boolean,
    won                     boolean,
    settled_in              text,
    goals                   integer,
    shots                   integer,
    hits                    integer,
    pim                     integer,
    power_play_opportunities integer,
    power_play_goals        integer,
    faceoff_win_pct         real,
    giveaways               integer,
    takeaways               integer,
    blocked                 integer,
    UNIQUE (game_id, team_id)
);

ALTER TABLE game_team_stats ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to game_team_stats" ON game_team_stats;
CREATE POLICY "Allow all access to game_team_stats"
    ON game_team_stats FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON game_team_stats TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE game_team_stats_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- game_advanced_stats — per-game per-situation analytics (Kaggle imports)
-- ============================================================
CREATE TABLE IF NOT EXISTS game_advanced_stats (
    id                              serial PRIMARY KEY,
    game_id                         integer NOT NULL REFERENCES games(id),
    team_id                         integer NOT NULL REFERENCES teams(id),
    situation                       text NOT NULL,
    is_home                         boolean,
    x_goals_pct                     real,
    corsi_pct                       real,
    fenwick_pct                     real,
    ice_time                        real,
    x_goals_for                     real,
    x_goals_against                 real,
    goals_for                       integer,
    goals_against                   integer,
    shots_on_goal_for               integer,
    shots_on_goal_against           integer,
    shot_attempts_for               integer,
    shot_attempts_against           integer,
    high_danger_shots_for           integer,
    high_danger_shots_against       integer,
    high_danger_goals_for           integer,
    high_danger_goals_against       integer,
    high_danger_x_goals_for         real,
    high_danger_x_goals_against     real,
    medium_danger_shots_for         integer,
    medium_danger_shots_against     integer,
    low_danger_shots_for            integer,
    low_danger_shots_against        integer,
    faceoffs_won_for                integer,
    faceoffs_won_against            integer,
    hits_for                        integer,
    hits_against                    integer,
    takeaways_for                   integer,
    takeaways_against               integer,
    giveaways_for                   integer,
    giveaways_against               integer,
    penalties_for                   integer,
    penalties_against               integer,
    penalty_minutes_for             integer,
    penalty_minutes_against         integer,
    UNIQUE (game_id, team_id, situation)
);

ALTER TABLE game_advanced_stats ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to game_advanced_stats" ON game_advanced_stats;
CREATE POLICY "Allow all access to game_advanced_stats"
    ON game_advanced_stats FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON game_advanced_stats TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE game_advanced_stats_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- game_skater_stats — per-game per-player stats (Kaggle imports)
-- ============================================================
CREATE TABLE IF NOT EXISTS game_skater_stats (
    id                          serial PRIMARY KEY,
    game_id                     integer NOT NULL REFERENCES games(id),
    player_id                   integer NOT NULL,
    team_id                     integer NOT NULL REFERENCES teams(id),
    time_on_ice                 integer,
    goals                       integer,
    assists                     integer,
    shots                       integer,
    hits                        integer,
    power_play_goals            integer,
    power_play_assists          integer,
    penalty_minutes             integer,
    faceoff_wins                integer,
    faceoff_taken               integer,
    takeaways                   integer,
    giveaways                   integer,
    short_handed_goals          integer,
    short_handed_assists        integer,
    blocked                     integer,
    plus_minus                  integer,
    even_time_on_ice            integer,
    short_handed_time_on_ice    integer,
    power_play_time_on_ice      integer,
    UNIQUE (game_id, player_id)
);

ALTER TABLE game_skater_stats ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to game_skater_stats" ON game_skater_stats;
CREATE POLICY "Allow all access to game_skater_stats"
    ON game_skater_stats FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON game_skater_stats TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE game_skater_stats_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- game_goalie_stats — per-game per-goalie stats (Kaggle imports)
-- ============================================================
CREATE TABLE IF NOT EXISTS game_goalie_stats (
    id                              serial PRIMARY KEY,
    game_id                         integer NOT NULL REFERENCES games(id),
    player_id                       integer NOT NULL,
    team_id                         integer NOT NULL REFERENCES teams(id),
    time_on_ice                     integer,
    assists                         integer,
    goals                           integer,
    pim                             integer,
    shots_against                   integer,
    saves                           integer,
    power_play_saves                integer,
    short_handed_saves              integer,
    even_saves                      integer,
    short_handed_shots_against      integer,
    even_shots_against              integer,
    power_play_shots_against        integer,
    decision                        text,
    save_pct                        real,
    power_play_save_pct             real,
    even_strength_save_pct          real,
    UNIQUE (game_id, player_id)
);

ALTER TABLE game_goalie_stats ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to game_goalie_stats" ON game_goalie_stats;
CREATE POLICY "Allow all access to game_goalie_stats"
    ON game_goalie_stats FOR ALL
    USING (true) WITH CHECK (true);

GRANT ALL ON game_goalie_stats TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE game_goalie_stats_id_seq TO anon, authenticated, service_role;

-- Kaggle table indexes
CREATE INDEX IF NOT EXISTS idx_game_team_stats_game ON game_team_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_game_team_stats_team ON game_team_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_game_advanced_stats_game ON game_advanced_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_game_advanced_stats_team ON game_advanced_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_game_advanced_stats_situation ON game_advanced_stats(game_id, situation);
CREATE INDEX IF NOT EXISTS idx_game_skater_stats_game ON game_skater_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_game_skater_stats_player ON game_skater_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_game_skater_stats_team ON game_skater_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_game_goalie_stats_game ON game_goalie_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_game_goalie_stats_player ON game_goalie_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_game_goalie_stats_team ON game_goalie_stats(team_id);
