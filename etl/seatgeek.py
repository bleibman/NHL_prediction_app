"""SeatGeek ticket price ETL — fetch upcoming NHL event prices and upsert snapshots."""

import logging
from datetime import date

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import SEATGEEK_API_BASE, SEATGEEK_CLIENT_ID
from db.supabase import select, upsert

logger = logging.getLogger(__name__)

# SeatGeek performer names that don't match our teams.name exactly
_NAME_OVERRIDES: dict[str, str] = {
    "Montreal Canadiens": "Canadiens de Montréal",
    "Montréal Canadiens": "Canadiens de Montréal",
}


def _build_session() -> requests.Session:
    """Create a requests Session with retry for SeatGeek API."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _get_team_name_to_id_map() -> dict[str, int]:
    """Build a case-insensitive team name → id lookup from the DB."""
    teams = select("teams", columns="id,name")
    mapping: dict[str, int] = {}
    for t in teams:
        mapping[t["name"].lower()] = t["id"]
    return mapping


def _resolve_team_id(performer_name: str, team_map: dict[str, int]) -> int | None:
    """Map a SeatGeek performer name to our team ID."""
    # Apply overrides first
    name = _NAME_OVERRIDES.get(performer_name, performer_name)
    return team_map.get(name.lower())


def fetch_and_upsert_ticket_snapshots():
    """Fetch upcoming NHL events from SeatGeek and upsert ticket price snapshots.

    Gracefully returns if SEATGEEK_CLIENT_ID is not configured.
    Idempotent: running multiple times per day overwrites the same snapshot rows.
    """
    if not SEATGEEK_CLIENT_ID:
        logger.info("SEATGEEK_CLIENT_ID not set — skipping ticket price fetch")
        return

    team_map = _get_team_name_to_id_map()
    if not team_map:
        logger.warning("No teams in database — run teams ETL first")
        return

    session = _build_session()
    today = date.today()

    snapshot_rows: list[dict] = []
    venue_rows: list[dict] = []
    page = 1
    per_page = 100

    while True:
        params = {
            "client_id": SEATGEEK_CLIENT_ID,
            "taxonomies.name": "nhl",
            "per_page": per_page,
            "page": page,
        }

        try:
            resp = session.get(f"{SEATGEEK_API_BASE}/events", params=params, timeout=30)
            resp.raise_for_status()
        except Exception:
            logger.warning("SeatGeek API request failed (page %d)", page, exc_info=True)
            break

        data = resp.json()
        events = data.get("events", [])
        if not events:
            break

        for event in events:
            performers = event.get("performers", [])
            if not performers:
                continue

            # Determine home and away teams
            home_team_id = None
            away_team_id = None
            for perf in performers:
                perf_name = perf.get("name", "")
                team_id = _resolve_team_id(perf_name, team_map)
                if team_id is None:
                    continue
                if perf.get("home_team"):
                    home_team_id = team_id
                else:
                    away_team_id = team_id

            if not home_team_id:
                continue

            # Extract stats
            stats = event.get("stats", {})
            avg_price = stats.get("average_price")
            lowest_price = stats.get("lowest_price")
            highest_price = stats.get("highest_price")
            listing_count = stats.get("listing_count")

            # Parse game date
            datetime_utc = event.get("datetime_utc", "")
            game_date = datetime_utc[:10] if datetime_utc else None

            snapshot_rows.append({
                "seatgeek_event_id": event["id"],
                "game_date": game_date,
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "snapshot_date": today.isoformat(),
                "lowest_price": lowest_price,
                "average_price": avg_price,
                "highest_price": highest_price,
                "listing_count": listing_count,
            })

            # Extract venue info for upsert
            venue = event.get("venue", {})
            if venue and home_team_id:
                venue_rows.append({
                    "team_id": home_team_id,
                    "name": venue.get("name"),
                    "city": venue.get("city"),
                    "state": venue.get("state"),
                    "capacity": venue.get("capacity"),
                })

        # Pagination — check if we have more
        meta = data.get("meta", {})
        total = meta.get("total", 0)
        if page * per_page >= total:
            break
        page += 1

    # Upsert venues (deduplicate by team_id)
    if venue_rows:
        seen_teams: set[int] = set()
        unique_venues: list[dict] = []
        for v in venue_rows:
            if v["team_id"] not in seen_teams:
                seen_teams.add(v["team_id"])
                unique_venues.append(v)
        upsert("venues", unique_venues, on_conflict="team_id")
        logger.info("Upserted %d venues", len(unique_venues))

    # Upsert ticket snapshots
    if snapshot_rows:
        upsert("ticket_snapshots", snapshot_rows, on_conflict="seatgeek_event_id,snapshot_date")
        logger.info("Upserted %d ticket snapshots for %s", len(snapshot_rows), today)
    else:
        logger.info("No ticket snapshots to upsert")
