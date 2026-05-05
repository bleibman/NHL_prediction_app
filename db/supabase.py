"""Supabase REST API client (public schema)."""

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)


def _build_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.headers.update({
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    })
    return session


_session = _build_session()


def _url(table: str) -> str:
    base = SUPABASE_URL.rstrip("/")
    return f"{base}/{table}"


# ------------------------------------------------------------------
# Read
# ------------------------------------------------------------------

def select(
    table: str,
    columns: str = "*",
    filters: dict[str, str] | None = None,
    order: str | None = None,
    limit: int | None = None,
    timeout: int = 120,
) -> list[dict]:
    """SELECT rows from a table.

    Automatically paginates when the server returns its max-rows limit
    (typically 1000) to fetch all matching rows.

    filters maps column names to PostgREST filter expressions,
    e.g. {"season_id": "eq.20242025", "points": "gt.90"}.
    """
    params: dict[str, Any] = {"select": columns}
    if filters:
        params.update(filters)
    if order:
        params["order"] = order
    if limit:
        params["limit"] = str(limit)
        resp = _session.get(_url(table), params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    # No explicit limit — paginate to get all rows
    page_size = 1000
    all_rows: list[dict] = []
    offset = 0

    while True:
        params["limit"] = str(page_size)
        params["offset"] = str(offset)
        resp = _session.get(_url(table), params=params, timeout=timeout)
        resp.raise_for_status()
        batch = resp.json()
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    return all_rows


# ------------------------------------------------------------------
# Write
# ------------------------------------------------------------------

def upsert(table: str, rows: list[dict], on_conflict: str | None = None) -> list[dict]:
    """Upsert rows into a table (INSERT ... ON CONFLICT UPDATE).

    on_conflict: comma-separated column names for conflict resolution,
    e.g. "season_id,team_id".  Uses the table's unique constraint by default.
    """
    if not rows:
        return []

    batch_size = 200
    all_results: list[dict] = []

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        headers = {
            "Prefer": "resolution=merge-duplicates,return=representation",
        }
        params = {}
        if on_conflict:
            params["on_conflict"] = on_conflict

        resp = _session.post(
            _url(table), json=batch, headers=headers, params=params, timeout=120,
        )
        if resp.status_code >= 400:
            logger.error(
                "Upsert to %s failed (%d): %s",
                table, resp.status_code, resp.text[:500],
            )
            resp.raise_for_status()
        all_results.extend(resp.json())

    return all_results


def insert(table: str, rows: list[dict]) -> list[dict]:
    """Plain INSERT (no conflict handling)."""
    if not rows:
        return []

    headers = {"Prefer": "return=representation"}
    resp = _session.post(_url(table), json=rows, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def update(table: str, data: dict, filters: dict[str, str]) -> list[dict]:
    """PATCH rows matching filters with the given data."""
    headers = {"Prefer": "return=representation"}
    resp = _session.patch(
        _url(table), json=data, headers=headers, params=filters, timeout=120,
    )
    if resp.status_code >= 400:
        logger.error("Update %s failed (%d): %s", table, resp.status_code, resp.text[:500])
        resp.raise_for_status()
    return resp.json()


def delete(table: str, filters: dict[str, str]) -> None:
    """DELETE rows matching filters."""
    resp = _session.delete(_url(table), params=filters, timeout=30)
    resp.raise_for_status()


def rpc(func_name: str, params: dict | None = None):
    """Call a Supabase RPC (database function)."""
    base = SUPABASE_URL.rstrip("/").replace("/rest/v1", "")
    url = f"{base}/rest/v1/rpc/{func_name}"
    resp = _session.post(url, json=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()
