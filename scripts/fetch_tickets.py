#!/usr/bin/env python3
"""Daily SeatGeek ticket snapshot fetch (called by GitHub Actions)."""

import logging
import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.seatgeek import fetch_and_upsert_ticket_snapshots


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    logger = logging.getLogger("fetch_tickets")
    logger.info("=== Fetching ticket snapshots ===")
    fetch_and_upsert_ticket_snapshots()
    logger.info("=== Done ===")


if __name__ == "__main__":
    main()
