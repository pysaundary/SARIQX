import logging
import traceback
from multiprocessing import Queue
from loguru import logger

class TunnelQueueHandler(logging.Handler):
    """
    Standard Python logging interface jo saare standard logs ko
    multiprocessing queue mein push karega bina event loop block kiye.
    """
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        try:
            # Format message
            msg = self.format(record)
            # Put inside queue without blocking the main event loop
            self.queue.put_nowait({"level": record.levelname, "message": msg})
        except Exception:
            self.handleError(record)

def setup_app_logging_client(queue: Queue):
    """
    FastAPI worker thread start hote hi isko call karenge.
    Yeh standard uvicorn loggers ka gala ghotega aur unhe queue mein divert karega.
    """
    def queue_loguru_message(message):
        try:
            record = message.record
            rendered_message = record["message"]
            if record["exception"]:
                rendered_message = (
                    f"{rendered_message}\n"
                    f"{''.join(traceback.format_exception(record['exception'].type, record['exception'].value, record['exception'].traceback)).rstrip()}"
                )

            queue.put_nowait({"level": record["level"].name, "message": rendered_message})
        except Exception:
            traceback.print_exc()

    # 1. Main process ke loguru ko config karo ki wo sirf queue mein push kare
    logger.remove()
    logger.add(
        queue_loguru_message,
        level="INFO",
        colorize=False
    )

    # 2. Uvicorn aur standard routing frameworks ko intercept karo
    intercept_handler = TunnelQueueHandler(queue)
    
    # Saare block-prone internal loggers ki list
    seen_loggers = [
        logging.getLogger("uvicorn"),
        logging.getLogger("uvicorn.access"),
        logging.getLogger("uvicorn.error"),
        logging.getLogger("fastapi")
    ]

    for log in seen_loggers:
        log.handlers = [intercept_handler]
        log.propagate = False
        log.setLevel(logging.INFO)

    logger.info("🚀 SARIQX Async Logging Client hooked to Inter-Process Queue.")
