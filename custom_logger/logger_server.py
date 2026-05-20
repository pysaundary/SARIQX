import sys
import signal
import traceback
from multiprocessing import Queue
from loguru import logger

def logger_worker_process(queue: Queue, log_file_path: str = "logs/sariqx.log"):
    """
    Isolated Worker Process Boundary with Enforced Graceful Shutdown.
    """
    # ⚡ CRITICAL: Ignore SIGINT (Ctrl+C) in this child process!
    # Terminal ka Ctrl+C pooray process group ko signal bhejta hai. 
    # Hum isko bol rahe hain ki tu andha ho ja, direct signal pe mat mar.
    # Tu sirf tabhi marega jab main process se Queue mein 'None' aayega.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Loguru Sinks Setup
    logger.remove()
    
    # Console
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{process.name}</cyan>:<cyan>{thread.name}</cyan> - <level>{message}</level>",
        colorize=True,
        level="INFO"
    )

    # File
    logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {process.name}:{thread.name} - {message}",
        level="INFO",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        enqueue=False
    )

    logger.info("⚡ SARIQX Logger Server Process Initialized Successfully.")

    # 🔄 Endless Consumer Loop
    while True:
        try:
            # Main app se message ka wait karo
            record = queue.get()
            
            # 💊 POISON PILL CHECK: Agar None aaya, matlab main app safely band ho chuka hai
            if record is None:
                logger.info("Poison Pill received. Flushing logs and stopping SARIQX Logger Server cleanly...")
                break
                
            # Log ko safely disk/console pe likho
            logger.log(record["level"], record["message"])
            
        except Exception as e:
            print(f"CRITICAL ERROR IN SARIQX LOGGER SERVER: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            break

    # Loop ke bahar aane par resource cleanup confirmation
    print("🔒 SARIQX Logger Server Process terminated with status 0 (Clean Cleanup).", file=sys.stdout)
