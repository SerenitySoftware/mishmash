"""Server-Sent Events for real-time run status updates."""
import asyncio
import json
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.config import settings

router = APIRouter(prefix="/api/events", tags=["events"])


async def run_status_stream(run_id: str):
    """Generator that yields SSE events for a run's status changes."""
    r = aioredis.from_url(settings.redis_url)
    pubsub = r.pubsub()
    channel = f"run:{run_id}"

    try:
        await pubsub.subscribe(channel)

        # Send initial ping
        yield f"event: ping\ndata: {json.dumps({'run_id': run_id})}\n\n"

        timeout_count = 0
        while timeout_count < 60:  # Max 5 minutes (60 * 5s)
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True), timeout=5.0
                )
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    yield f"event: status\ndata: {json.dumps(data)}\n\n"

                    # Stop streaming if run is done
                    if data.get("status") in ("completed", "failed"):
                        yield f"event: done\ndata: {json.dumps(data)}\n\n"
                        break
                else:
                    # Send keepalive
                    yield f"event: ping\ndata: {json.dumps({'keepalive': True})}\n\n"
                    timeout_count += 1
            except asyncio.TimeoutError:
                yield f"event: ping\ndata: {json.dumps({'keepalive': True})}\n\n"
                timeout_count += 1
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await r.close()


@router.get("/runs/{run_id}/stream")
async def stream_run_status(run_id: uuid.UUID):
    """SSE endpoint for real-time run status updates."""
    return StreamingResponse(
        run_status_stream(str(run_id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
