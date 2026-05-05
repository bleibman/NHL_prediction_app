#!/usr/bin/env python3
"""Import Kaggle NHL datasets into the database.

Usage:
    python scripts/import_kaggle.py                     # All imports (skips player stats)
    python scripts/import_kaggle.py --attendance-only    # Just attendance
    python scripts/import_kaggle.py --team-stats-only    # Just game_team_stats
    python scripts/import_kaggle.py --advanced-only      # Just game_advanced_stats
    python scripts/import_kaggle.py --player-stats-only  # Just skater + goalie (945k+ rows)
    python scripts/import_kaggle.py --all                # Everything including player stats
    python scripts/import_kaggle.py --dry-run            # Parse & match, no DB writes
"""

import argparse
import logging
import os
import sys
import time

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.kaggle_attendance import import_attendance
from etl.kaggle_game_team_stats import import_game_team_stats
from etl.kaggle_advanced_stats import import_advanced_stats
from etl.kaggle_game_player_stats import import_player_stats


def main():
    parser = argparse.ArgumentParser(
        description="Import Kaggle NHL datasets into the database"
    )
    parser.add_argument(
        "--attendance-only", action="store_true",
        help="Only import attendance data",
    )
    parser.add_argument(
        "--team-stats-only", action="store_true",
        help="Only import game team stats",
    )
    parser.add_argument(
        "--advanced-only", action="store_true",
        help="Only import advanced metrics",
    )
    parser.add_argument(
        "--player-stats-only", action="store_true",
        help="Only import skater + goalie stats (large)",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Import everything including player stats",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse and match but don't write to database",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    has_filter = any([
        args.attendance_only, args.team_stats_only,
        args.advanced_only, args.player_stats_only,
    ])

    if args.dry_run:
        logging.info("=== DRY RUN MODE — no database writes ===")

    start = time.time()

    # Phase 1: Attendance
    if not has_filter or args.attendance_only:
        logging.info("=" * 60)
        logging.info("Phase 1: Attendance import")
        logging.info("=" * 60)
        result = import_attendance(dry_run=args.dry_run)
        logging.info("Attendance results: %s", result)

    # Phase 2: Game team stats
    if not has_filter or args.team_stats_only:
        logging.info("=" * 60)
        logging.info("Phase 2: Game team stats import")
        logging.info("=" * 60)
        result = import_game_team_stats(dry_run=args.dry_run)
        logging.info("Game team stats results: %s", result)

    # Phase 3: Advanced metrics
    if not has_filter or args.advanced_only:
        logging.info("=" * 60)
        logging.info("Phase 3: Advanced metrics import")
        logging.info("=" * 60)
        count = import_advanced_stats(dry_run=args.dry_run)
        logging.info("Advanced metrics: %d rows", count)

    # Phase 4: Player stats (opt-in or --all)
    if args.player_stats_only or args.all:
        logging.info("=" * 60)
        logging.info("Phase 4: Player game stats import (large)")
        logging.info("=" * 60)
        result = import_player_stats(dry_run=args.dry_run)
        logging.info("Player stats results: %s", result)
    elif not has_filter:
        logging.info("Skipping player stats (use --all or --player-stats-only)")

    elapsed = time.time() - start
    logging.info("=" * 60)
    logging.info("Done in %.1f seconds", elapsed)


if __name__ == "__main__":
    main()
