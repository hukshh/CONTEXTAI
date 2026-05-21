import os
import json
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from services.status_manager import status_manager
from redis.asyncio import Redis as AsyncRedis

router = APIRouter()
logger = logging.getLogger(__name__)

async def status_event_generator():
    """
    Async generator that streams status updates from Redis PubSub channel.
    Falls back to in-memory queues if Redis is unavailable.
    """
    redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    
    # Try using Redis PubSub first
    try:
        async_redis = AsyncRedis.from_url(redis_url, decode_responses=True)
        pubsub = async_redis.pubsub()
        await pubsub.subscribe("file_status_updates")
        logger.info("SSE: Client subscribed to Redis channel 'file_status_updates'")
        
        while True:
            try:
                # Poll the pubsub subscription
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    data = message.get("data")
                    yield {
                        "event": "status_update",
                        "data": data
                    }
            except asyncio.CancelledError:
                logger.info("SSE: Client cancelled subscription (Redis)")
                break
            except Exception as e:
                logger.error(f"SSE: Error reading from Redis: {e}")
                await asyncio.sleep(2.0)
                
        await pubsub.unsubscribe("file_status_updates")
        await async_redis.close()
        return
        
    except Exception as e:
        logger.warning(f"SSE: Redis subscription failed, falling back to in-memory pub-sub: {e}")

    # Fallback to local in-memory listeners
    queue = asyncio.Queue()
    status_manager.in_memory_listeners.add(queue)
    logger.info("SSE: Client registered to in-memory listener queue")
    
    try:
        while True:
            try:
                # Wait for status updates pushed by the in-memory update_status
                state = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield {
                    "event": "status_update",
                    "data": json.dumps(state)
                }
            except asyncio.TimeoutError:
                # Send a keep-alive event
                yield {
                    "event": "ping",
                    "data": "keep-alive"
                }
            except asyncio.CancelledError:
                logger.info("SSE: Client cancelled subscription (In-Memory)")
                break
    finally:
        status_manager.in_memory_listeners.remove(queue)


@router.get("/files/stream-status")
async def stream_status():
    """
    Server-Sent Events endpoint streaming realtime document processing progress updates.
    """
    return EventSourceResponse(status_event_generator())


@router.get("/files/{filename}/status")
async def get_file_status(filename: str):
    """
    HTTP endpoint to poll status of a specific file.
    """
    status = status_manager.get_status(filename)
    if not status or status.get("status") == "unknown":
        # Check if file exists in retrieval service or storage service
        from services.retrieval_service import retrieval_service
        # Reload to check
        retrieval_service.reload()
        if filename in retrieval_service.doc_to_ids:
            return {
                "filename": filename,
                "status": "ready",
                "progress": 100.0,
                "error": None
            }
        else:
            raise HTTPException(status_code=404, detail="File status not found")
            
    return status
