"""Fetch and upsert NHL teams."""

import logging

from db.supabase import select, upsert
from etl.api_client import get_web

logger = logging.getLogger(__name__)


def fetch_and_upsert_teams():
    """Pull current team list from standings and upsert into DB.

    The standings endpoint provides abbreviation/name/division/conference
    but no numeric team ID.  We resolve IDs from the club-schedule endpoint.
    """
    logger.info("Fetching teams from standings")
    data = get_web("standings/now")
    standings = data.get("standings", [])

    seen: set[str] = set()
    rows: list[dict] = []
    for entry in standings:
        raw = entry.get("teamAbbrev", {})
        abbrev = raw.get("default", "") if isinstance(raw, dict) else str(raw)
        if not abbrev or abbrev in seen:
            continue
        seen.add(abbrev)

        raw_name = entry.get("teamName", {})
        name = raw_name.get("default", "") if isinstance(raw_name, dict) else str(raw_name)

        rows.append({
            "abbreviation": abbrev,
            "name": name,
            "division": entry.get("divisionName", ""),
            "conference": entry.get("conferenceName", ""),
        })

    # Resolve numeric team IDs via the club-schedule endpoint
    _resolve_team_ids(rows)

    to_upsert = [r for r in rows if r.get("id") is not None]
    if to_upsert:
        upsert("teams", to_upsert, on_conflict="id")
    logger.info("Upserted %d teams", len(to_upsert))


def _resolve_team_ids(rows: list[dict]):
    """Use club-schedule endpoint to find numeric team IDs."""
    for row in rows:
        abbrev = row["abbreviation"]
        try:
            data = get_web(f"club-schedule-season/{abbrev}/20242025")
            for game in data.get("games", []):
                for side in ("homeTeam", "awayTeam"):
                    team = game.get(side, {})
                    if team.get("abbrev") == abbrev:
                        row["id"] = team["id"]
                        break
                if row.get("id"):
                    break
        except Exception:
            logger.warning("Could not resolve ID for %s", abbrev, exc_info=True)


def get_team_abbrev_to_id_map() -> dict[str, int]:
    """Return {abbreviation: team_id} from the DB."""
    teams = select("teams", columns="id,abbreviation")
    return {t["abbreviation"]: t["id"] for t in teams}
