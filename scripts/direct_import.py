#!/usr/bin/env python3
"""Direct SQL import of Kaggle data via psycopg2 (bypasses REST API)."""
import csv, os, sys, time
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etl.kaggle_mappings import COLETTI_TEAM_ID_MAP, TEAM_NAME_TO_ID

DB = dict(
    host='db.dcxjyjlrlrtjbnaxlymu.supabase.co', port=5432,
    dbname='postgres', user='postgres', password='KpCc4Ykev8GBj#?',
    connect_timeout=30, options='-c statement_timeout=600000',
)
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def log(msg): print(msg, flush=True)

def si(v):
    if not v or str(v).strip().lower() in ("", "nan", "none"): return None
    try: return int(float(str(v).strip()))
    except: return None

def sf(v):
    if not v or str(v).strip().lower() in ("", "nan", "none"): return None
    try: return float(str(v).strip())
    except: return None

def sb(v):
    if v is None or v == "": return None
    s = str(v).strip().upper()
    if s in ("TRUE","T","1"): return True
    if s in ("FALSE","F","0"): return False
    return None

conn = psycopg2.connect(**DB)
conn.autocommit = False
cur = conn.cursor()
start = time.time()

# ── Lookups ──
log("Loading lookups...")
cur.execute("SELECT id, game_date, home_team_id FROM games")
game_lookup = {}
for gid, gdate, htid in cur.fetchall():
    if gdate and htid:
        game_lookup[(str(gdate), htid)] = gid
cur.execute("SELECT id FROM teams")
valid_teams = {r[0] for r in cur.fetchall()}
valid_games = set(game_lookup.values())
log(f"  {len(game_lookup)} games, {len(valid_teams)} teams")

# ═══ Phase 1a: Coletti attendance ═══
csv_path = os.path.join(DATA, "coletti", "nhl_dataset.csv")
if os.path.isfile(csv_path):
    log("\nPhase 1a: Coletti attendance...")
    updates = []
    for row in csv.DictReader(open(csv_path, encoding="utf-8")):
        if row.get("home_away") != "home": continue
        att = si(row.get("attendance"))
        if not att or att <= 0: continue
        ds = row.get("date", "")
        try: gd = datetime.fromisoformat(ds).strftime("%Y-%m-%d")
        except: gd = ds[:10] if len(ds) >= 10 else None
        if not gd: continue
        eid = si(row.get("team_id"))
        if not eid: continue
        tid = COLETTI_TEAM_ID_MAP.get(eid)
        if not tid: continue
        gid = game_lookup.get((gd, tid))
        if not gid: continue
        updates.append((att, gid))
    if updates:
        cur.executemany("UPDATE games SET attendance=%s WHERE id=%s", updates)
        conn.commit()
    log(f"  Coletti: {len(updates)} games updated")

# ═══ Phase 1b: Flynn28 attendance ═══
csv_path = os.path.join(DATA, "flynn28", "data.csv")
if os.path.isfile(csv_path):
    log("\nPhase 1b: Flynn28 attendance...")
    cur.execute("SELECT id FROM games WHERE attendance IS NOT NULL")
    has_att = {r[0] for r in cur.fetchall()}
    updates = []
    for row in csv.DictReader(open(csv_path, encoding="utf-8")):
        ds = row.get("Date", "")
        if not ds or ds < "2005-": continue
        att = si(row.get("Attendance"))
        if not att or att <= 0: continue
        gd = ds[:10]
        tid = TEAM_NAME_TO_ID.get(row.get("Home", "").strip())
        if not tid: continue
        gid = game_lookup.get((gd, tid))
        if not gid or gid in has_att: continue
        updates.append((att, gid))
        has_att.add(gid)
    if updates:
        cur.executemany("UPDATE games SET attendance=%s WHERE id=%s", updates)
        conn.commit()
    log(f"  Flynn28: {len(updates)} games updated")

# ═══ Phase 2: Game team stats ═══
csv_path = os.path.join(DATA, "game_teams_stats.csv")
if os.path.isfile(csv_path):
    log("\nPhase 2: Game team stats...")
    rows = []
    skipped = 0
    for row in csv.DictReader(open(csv_path, encoding="utf-8")):
        gid = si(row.get("game_id"))
        tid = si(row.get("team_id"))
        if not gid or not tid or gid not in valid_games or tid not in valid_teams:
            skipped += 1; continue
        is_home = sb(row.get("HoA") == "home") if "HoA" in row else sb(row.get("is_home"))
        rows.append((
            gid, tid, is_home, sb(row.get("won")), row.get("settled_in") or None,
            si(row.get("goals")), si(row.get("shots")), si(row.get("hits")), si(row.get("pim")),
            si(row.get("powerPlayOpportunities") or row.get("power_play_opportunities")),
            si(row.get("powerPlayGoals") or row.get("power_play_goals")),
            sf(row.get("faceOffWinPercentage") or row.get("faceoff_win_pct")),
            si(row.get("giveaways")), si(row.get("takeaways")), si(row.get("blocked")),
        ))
    if rows:
        execute_values(cur, """
            INSERT INTO game_team_stats (
                game_id, team_id, is_home, won, settled_in,
                goals, shots, hits, pim,
                power_play_opportunities, power_play_goals,
                faceoff_win_pct, giveaways, takeaways, blocked
            ) VALUES %s ON CONFLICT (game_id, team_id) DO NOTHING
        """, rows, page_size=500)
        conn.commit()
    log(f"  Game team stats: {len(rows)} inserted, {skipped} skipped")

# ═══ Phase 3: Advanced stats ═══
adv_csv = os.path.join(DATA, "mexwell", "all_teams.csv")
if os.path.isfile(adv_csv):
    log("\nPhase 3: Advanced stats...")
    # Check columns first
    with open(adv_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        first = next(reader)
        cols = list(first.keys())
        log(f"  Columns: {cols[:10]}...")

    # mexwell uses game_id column directly (NHL game IDs)
    if "game_id" in cols:
        rows = []
        skipped = 0
        for row in csv.DictReader(open(adv_csv, encoding="utf-8")):
            gid = si(row.get("game_id"))
            tid = si(row.get("team_id"))
            sit = row.get("situation", "").strip()
            if not gid or not tid or not sit or gid not in valid_games or tid not in valid_teams:
                skipped += 1; continue
            rows.append((
                gid, tid, sit,
                sb(row.get("is_home")),
                sf(row.get("xGoalsPercentage") or row.get("x_goals_pct")),
                sf(row.get("corsiPercentage") or row.get("corsi_pct")),
                sf(row.get("fenwickPercentage") or row.get("fenwick_pct")),
                sf(row.get("iceTime") or row.get("ice_time")),
                sf(row.get("xGoalsFor") or row.get("x_goals_for")),
                sf(row.get("xGoalsAgainst") or row.get("x_goals_against")),
                si(row.get("goalsFor") or row.get("goals_for")),
                si(row.get("goalsAgainst") or row.get("goals_against")),
                si(row.get("shotsOnGoalFor") or row.get("shots_on_goal_for")),
                si(row.get("shotsOnGoalAgainst") or row.get("shots_on_goal_against")),
                si(row.get("shotAttemptsFor") or row.get("shot_attempts_for")),
                si(row.get("shotAttemptsAgainst") or row.get("shot_attempts_against")),
            ))
        if rows:
            execute_values(cur, """
                INSERT INTO game_advanced_stats (
                    game_id, team_id, situation, is_home,
                    x_goals_pct, corsi_pct, fenwick_pct, ice_time,
                    x_goals_for, x_goals_against,
                    goals_for, goals_against,
                    shots_on_goal_for, shots_on_goal_against,
                    shot_attempts_for, shot_attempts_against
                ) VALUES %s ON CONFLICT (game_id, team_id, situation) DO NOTHING
            """, rows, page_size=500)
            conn.commit()
        log(f"  Advanced stats: {len(rows)} inserted, {skipped} skipped")
    else:
        log("  No game_id column found in mexwell CSV — skipping")

# ═══ Summary ═══
cur.execute("SELECT count(*) FROM games WHERE attendance IS NOT NULL")
att = cur.fetchone()[0]
cur.execute("SELECT count(*) FROM game_team_stats")
gts = cur.fetchone()[0]
cur.execute("SELECT count(*) FROM game_advanced_stats")
adv = cur.fetchone()[0]
elapsed = time.time() - start
log(f"\n{'='*60}")
log(f"Done in {elapsed:.1f}s")
log(f"  games with attendance: {att}")
log(f"  game_team_stats: {gts}")
log(f"  game_advanced_stats: {adv}")
cur.close()
conn.close()
