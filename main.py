import multiprocessing
import uvloop

# ⚡ Force-install uvloop at the absolute entrypoint
uvloop.install()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.logger_client import setup_app_logging_client
from custom_logger.logger_server import logger_worker_process

# 1. IPC Shared Memory Queue & Logger Server Spawning
log_queue = multiprocessing.Queue(-1)
logger_process = multiprocessing.Process(
    target=logger_worker_process, 
    args=(log_queue, "logs/sariqx_runtime.log"),
    name="SARIQX-Logger-Daemon"
)
logger_process.daemon = True
logger_process.start()

setup_app_logging_client(log_queue)


# ⚡ THE HARDENED LIFESPAN HANDSHAKE CONTROL
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🪐 [STARTUP ZONE]
    from app.core.config import load_sariqx_config
    from loguru import logger
    
    # Step 1: Pydantic settings parse karo aur memory variables lock karo
    load_sariqx_config()
    
    # Step 2: Connection pools import karo validation ke baad
    from app.db.postgres import async_engine
    from sqlalchemy import text
    from app.db.mongo import mongo_manager
    
    # === RELATIONAL COUPLING POOL CHECK ===
    logger.info("Warming up PostgreSQL Async Connection Pool...")
    try:
        async with async_engine.connect() as conn:
            # Clean strict execution wrapper
            await conn.execute(text("SELECT 1"))
        logger.info("✅ PostgreSQL Async Pool connection verified and warm.")
    except Exception as e:
        logger.critical(f"💥 PostgreSQL initialization crashed: {e}")
        raise SystemExit(1)
        
    # === DOCUMENT COUPLING POOL CHECK ===
    logger.info("Warming up MongoDB Motor Connection Pool...")
    try:
        mongo_manager.initialize_pool()
        # Trigger an implicit runtime ping to test authentication wire
        await mongo_manager.client.admin.command('ping')
        logger.info("✅ MongoDB Async Authenticated Pool connection verified and warm.")
    except Exception as e:
        logger.critical(f"💥 MongoDB Secured Connection failed! Authentication error: {e}")
        raise SystemExit(1) 
        
    yield  # SARIQX active pipeline starts handling incoming traffic strings
    
    # 🏁 [SHUTDOWN ZONE]
    logger.info("Lifespan shutdown sequence initiated. Flushing assets...")
    
    # Close Relational Engine
    await async_engine.dispose()
    logger.info("PostgreSQL connection pool disposed cleanly.")
    
    # Close Document Engine
    await mongo_manager.close_pool()
    
    # Finalize log pipelines safely without leaks
    log_queue.put(None)
    logger_process.join()
    log_queue.close()
    log_queue.join_thread()
    print("🏁 SARIQX App Engine fully closed. Absolute Graceful Stop Achieved.")  
    
# 2. FastAPI Engine Core Instantiation with Lifespan handler
app = FastAPI(
    title="SARIQX Engine",
    description="Multi-Tenant High-Velocity Doubt Resolution SaaS Backend",
    version="1.0.0",
    lifespan=lifespan
)

# 🔄 Lazy loading of Middlewares after app birth to avoid configuration timing leaks
from app.core.collector import collector

# 🔐 SECURITY MIDDLEWARE LEVEL 1: Trusted Host Guard via Pydantic Caching
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=collector.get("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
)

# 🔐 SECURITY MIDDLEWARE LEVEL 2: CORS Header Policy Origin Router via Pydantic Caching
app.add_middleware(
    CORSMiddleware,
    allow_origins=collector.get("CORS_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root_ping():
    from loguru import logger
    logger.info("Ping endpoint hit - Testing block-free architecture pipeline")
    return {"status": "online", "engine": "SARIQX Hardened Core"}