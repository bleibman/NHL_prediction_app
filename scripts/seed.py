#!/usr/bin/env python3
"""CLI script to run the full ETL pipeline."""

import argparse
import logging
import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.teams import fetch_and_upsert_teams
from etl.seasons import fetch_and_upsert_seasons
from etl.games import fetch_and_upsert_games
from etl.playoffs import fetch_and_upsert_playoffs
from etl.player_stats import fetch_and_upsert_player_stats


def main():
    parser = argparse.ArgumentParser(description="Seed the NHL database")
    parser.add_argument(
        "--season",
        type=int,
        default=None,
        help="Single season to refresh, e.g. 20232024. Default: all seasons.",
    )
    parser.add_argument(
        "--skip-games",
        action="store_true",
        help="Skip the (slow) games ETL step.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    logger = logging.getLogger("seed")

    logger.info("=== Starting ETL pipeline ===")
    logger.info("(Tables must already exist — run db/schema.sql in Supabase first)")

    logger.info("Step 1/5: Teams")
    fetch_and_upsert_teams()

    logger.info("Step 2/5: Season stats")
    fetch_and_upsert_seasons(single_season=args.season)

    if not args.skip_games:
        logger.info("Step 3/5: Games")
        fetch_and_upsert_games(single_season=args.season)
    else:
        logger.info("Step 3/5: Games — SKIPPED")

    logger.info("Step 4/5: Playoffs")
    fetch_and_upsert_playoffs(single_season=args.season)

    logger.info("Step 5/5: Player stats")
    fetch_and_upsert_player_stats(single_season=args.season)

    logger.info("=== ETL pipeline complete ===")


if __name__ == "__main__":
    main()
