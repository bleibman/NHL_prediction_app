"""NHL API wrapper with retry, rate limiting, and error handling."""

import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import NHL_API_WEB, NHL_API_STATS

logger = logging.getLogger(__name__)

# Minimum delay between requests (seconds)
_REQUEST_DELAY = 0.5
_last_request_time = 0.0


def _rate_limit():
    """Enforce minimum delay between API calls."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _REQUEST_DELAY:
        time.sleep(_REQUEST_DELAY - elapsed)
    _last_request_time = time.time()


def _build_session() -> requests.Session:
    """Create a requests Session with automatic retry."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,  # 1s, 2s, 4s, 8s, 16s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_session = _build_session()


def get_web(path: str, params: dict | None = None) -> dict:
    """GET from api-web.nhle.com/v1/{path}."""
    url = f"{NHL_API_WEB}/{path.lstrip('/')}"
    return _get(url, params)


def get_stats(path: str, params: dict | None = None) -> dict:
    """GET from api.nhle.com/stats/rest/en/{path}."""
    url = f"{NHL_API_STATS}/{path.lstrip('/')}"
    return _get(url, params)


def _get(url: str, params: dict | None = None) -> dict:
    """Execute a rate-limited GET request and return parsed JSON."""
    _rate_limit()
    logger.debug("GET %s  params=%s", url, params)
    resp = _session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()
