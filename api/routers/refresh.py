"""Data refresh API endpoint with SSE streaming."""

import json
import asyncio
from functools import partial

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.schemas import RefreshRequest
from api import cache

router = APIRouter()


@router.post("/start")
async def refresh_start(body: RefreshRequest):
    from etl.teams import fetch_and_upsert_teams
    from etl.seasons import fetch_and_upsert_seasons
    from etl.games import fetch_and_upsert_games
    from etl.playoffs import fetch_and_upsert_playoffs
    from etl.player_stats import fetch_and_upsert_player_stats
    from etl.seatgeek import fetch_and_upsert_ticket_snapshots

    season_arg = body.season_id

    steps = [
        ("Teams", fetch_and_upsert_teams),
        ("Season Stats", partial(fetch_and_upsert_seasons, season_arg) if season_arg else fetch_and_upsert_seasons),
        ("Games", partial(fetch_and_upsert_games, season_arg) if season_arg else fetch_and_upsert_games),
        ("Playoffs", partial(fetch_and_upsert_playoffs, season_arg) if season_arg else fetch_and_upsert_playoffs),
        ("Player Stats", partial(fetch_and_upsert_player_stats, season_arg) if season_arg else fetch_and_upsert_player_stats),
        ("Ticket Prices", fetch_and_upsert_ticket_snapshots),
    ]

    async def stream():
        for i, (label, func) in enumerate(steps):
            yield f"data: {json.dumps({'step': i + 1, 'total': 6, 'label': label, 'status': 'running'})}\n\n"
            try:
                await asyncio.to_thread(func)
                yield f"data: {json.dumps({'step': i + 1, 'total': 6, 'label': label, 'status': 'done'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'step': i + 1, 'total': 6, 'label': label, 'status': 'error', 'error': str(e)})}\n\n"
                break
        cache.invalidate()
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
