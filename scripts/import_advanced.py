#!/usr/bin/env python3
"""Direct SQL import of mexwell advanced stats via psycopg2."""
import csv, os, sys, time
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etl.kaggle_mappings import normalize_moneypuck_abbrev

DB = dict(
    host='db.dcxjyjlrlrtjbnaxlymu.supabase.co', port=5432,
    dbname='postgres', user='postgres', password=os.environ['Database_PW'],
    connect_timeout=30, options='-c statement_timeout=600000',
)
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "mexwell", "all_teams.csv")

def log(msg): print(msg, flush=True)
def si(v):
    if not v or str(v).strip().lower() in ("","nan","none"): return None
    try: return int(float(str(v).strip()))
    except: return None
def sf(v):
    if not v or str(v).strip().lower() in ("","nan","none"): return None
    try: return float(str(v).strip())
    except: return None

conn = psycopg2.connect(**DB)
conn.autocommit = False
cur = conn.cursor()
start = time.time()

# Load lookups
log("Loading lookups...")
cur.execute("SELECT id FROM games")
valid_games = {r[0] for r in cur.fetchall()}
cur.execute("SELECT abbreviation, id FROM teams")
abbrev_to_id = {r[0]: r[1] for r in cur.fetchall()}
log(f"  {len(valid_games)} games, {len(abbrev_to_id)} team abbrevs")

log(f"Reading {CSV_PATH}...")
rows = []
skipped = 0
matched = 0
unmatched = 0

with open(CSV_PATH, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        game_id = si(row.get("gameId"))
        if not game_id or game_id not in valid_games:
            skipped += 1
            continue

        raw_abbrev = row.get("playerTeam", "").strip()
        abbrev = normalize_moneypuck_abbrev(raw_abbrev)
        team_id = abbrev_to_id.get(abbrev)
        if not team_id:
            unmatched += 1
            continue

        situation = row.get("situation", "").strip()
        if not situation:
            skipped += 1
            continue

        hoa = row.get("home_or_away", "").strip().upper()
        rows.append((
            game_id, team_id, situation, hoa == "HOME",
            sf(row.get("xGoalsPercentage")),
            sf(row.get("corsiPercentage")),
            sf(row.get("fenwickPercentage")),
            sf(row.get("iceTime")),
            sf(row.get("xGoalsFor")),
            sf(row.get("xGoalsAgainst")),
            si(row.get("goalsFor")),
            si(row.get("goalsAgainst")),
            si(row.get("shotsOnGoalFor")),
            si(row.get("shotsOnGoalAgainst")),
            si(row.get("shotAttemptsFor")),
            si(row.get("shotAttemptsAgainst")),
        ))
        matched += 1

log(f"  Matched: {matched}, Skipped: {skipped}, Unmatched team: {unmatched}")
log(f"Inserting {len(rows)} rows...")

if rows:
    # Batch insert using execute_values for speed
    execute_values(cur, """
        INSERT INTO game_advanced_stats (
            game_id, team_id, situation, is_home,
            x_goals_pct, corsi_pct, fenwick_pct, ice_time,
            x_goals_for, x_goals_against,
            goals_for, goals_against,
            shots_on_goal_for, shots_on_goal_against,
            shot_attempts_for, shot_attempts_against
        ) VALUES %s ON CONFLICT (game_id, team_id, situation) DO NOTHING
    """, rows, page_size=1000)
    conn.commit()
    log("  Committed!")

cur.execute("SELECT count(*) FROM game_advanced_stats")
count = cur.fetchone()[0]
elapsed = time.time() - start
log(f"\nDone in {elapsed:.1f}s — game_advanced_stats: {count} rows")
cur.close()
conn.close()
