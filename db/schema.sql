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
