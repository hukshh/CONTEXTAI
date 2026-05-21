import os
from celery import Celery
import logging

logger = logging.getLogger(__name__)

# Load Redis configuration
redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

# Initialize Celery app
celery_app = Celery(
    "contextai_tasks",
    broker=redis_url,
    backend=redis_url
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

@celery_app.task(name="tasks.process_document_task")
def process_document_task(file_path: str, filename: str) -> int:
    """
    Asynchronous Celery task to process the uploaded PDF document.
    """
    logger.info(f"Celery: Starting document processing for {filename} (Path: {file_path})")
    
    # Import locally to avoid circular dependencies and load models only in the worker process
    from services.rag_service import rag_service
    
    try:
        chunks_count = rag_service.process_document(file_path, filename)
        logger.info(f"Celery: Completed processing for {filename}. Extracted {chunks_count} chunks.")
        return chunks_count
    except Exception as e:
        logger.error(f"Celery: Failed to process document {filename}: {e}", exc_info=True)
        # Update status manager with error
        from services.status_manager import status_manager
        status_manager.update_status(filename, "failed", error=str(e))
        return 0
