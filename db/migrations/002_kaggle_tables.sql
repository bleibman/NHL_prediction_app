-- Kaggle import tables — per-game team stats, advanced metrics, player stats
-- Run this in the Supabase SQL Editor (Dashboard > SQL Editor)

-- ============================================================
-- game_team_stats — per-game per-team box score
-- Source: martinellis game_teams_stats.csv (2000–2020), coletti (2024–25)
-- ============================================================
CREATE TABLE IF NOT EXISTS game_team_stats (
    id                      serial PRIMARY KEY,
    game_id                 integer NOT NULL REFERENCES games(id),
    team_id                 integer NOT NULL REFERENCES teams(id),
    is_home                 boolean,
    won                     boolean,
    settled_in              text,            -- REG, OT, SO
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
-- game_advanced_stats — per-game per-situation analytics (xGoals, corsi, fenwick)
-- Source: mexwell all_teams.csv (2008–2022)
-- ============================================================
CREATE TABLE IF NOT EXISTS game_advanced_stats (
    id                              serial PRIMARY KEY,
    game_id                         integer NOT NULL REFERENCES games(id),
    team_id                         integer NOT NULL REFERENCES teams(id),
    situation                       text NOT NULL,       -- all, 5on5, 5on4, 4on5, other
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
-- game_skater_stats — per-game per-player stats
-- Source: martinellis game_skater_stats.csv (945k rows)
-- ============================================================
CREATE TABLE IF NOT EXISTS game_skater_stats (
    id                          serial PRIMARY KEY,
    game_id                     integer NOT NULL REFERENCES games(id),
    player_id                   integer NOT NULL,
    team_id                     integer NOT NULL REFERENCES teams(id),
    time_on_ice                 integer,         -- seconds
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
    even_time_on_ice            integer,         -- seconds
    short_handed_time_on_ice    integer,         -- seconds
    power_play_time_on_ice      integer,         -- seconds
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
-- game_goalie_stats — per-game per-goalie stats
-- Source: martinellis game_goalie_stats.csv (56k rows)
-- ============================================================
CREATE TABLE IF NOT EXISTS game_goalie_stats (
    id                              serial PRIMARY KEY,
    game_id                         integer NOT NULL REFERENCES games(id),
    player_id                       integer NOT NULL,
    team_id                         integer NOT NULL REFERENCES teams(id),
    time_on_ice                     integer,         -- seconds
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
    decision                        text,            -- W, L, O (or empty)
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

-- ============================================================
-- Indexes
-- ============================================================
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
