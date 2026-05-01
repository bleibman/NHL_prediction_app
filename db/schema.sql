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
