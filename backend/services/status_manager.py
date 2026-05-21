import os
import json
import redis
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StatusManager:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
        self.redis_client = None
        self.in_memory_statuses: Dict[str, Dict[str, Any]] = {}
        self.in_memory_listeners = set()
        
        try:
            self.redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("StatusManager: Connected to Redis successfully.")
        except Exception as e:
            logger.warning(f"StatusManager: Failed to connect to Redis, falling back to in-memory: {e}")
            self.redis_client = None

    def update_status(self, filename: str, status: str, progress: float = 0.0, error: Optional[str] = None, **kwargs):
        state = {
            "filename": filename,
            "status": status,
            "progress": round(progress, 1),
            "error": error,
            **kwargs
        }
        
        # Save state
        if self.redis_client:
            try:
                self.redis_client.set(f"status:{filename}", json.dumps(state), ex=86400) # Expire status in 24 hours
                self.redis_client.publish("file_status_updates", json.dumps(state))
            except Exception as e:
                logger.error(f"StatusManager: Redis update failed: {e}")
                # Fallback to in-memory state if Redis fails temporarily
                self.in_memory_statuses[filename] = state
        else:
            self.in_memory_statuses[filename] = state
            # Publish to local active SSE listeners
            for q in list(self.in_memory_listeners):
                try:
                    q.put_nowait(state)
                except Exception as ex:
                    pass

    def get_status(self, filename: str) -> Dict[str, Any]:
        if self.redis_client:
            try:
                val = self.redis_client.get(f"status:{filename}")
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.error(f"StatusManager: Failed to get status from Redis: {e}")
        
        # Fallback or default
        return self.in_memory_statuses.get(filename, {
            "filename": filename,
            "status": "unknown",
            "progress": 0.0,
            "error": None
        })

status_manager = StatusManager()
