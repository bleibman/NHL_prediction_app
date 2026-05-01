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

ALTER TABLE games ADD COLUMN IF NOT EXISTS attendance integer;

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
