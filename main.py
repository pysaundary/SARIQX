import multiprocessing
import traceback
import uvloop
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text

# ⚡ Global High-Velocity Event Loop Installation at the Absolute Entrypoint
uvloop.install()

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


# ⚡ THE DECOUPLED LIFESPAN ORCHESTRATOR
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🪐 [STARTUP ZONE]
    from app.core.config import load_sariqx_config
    from loguru import logger
    
    # Step 1: Pydantic settings parse karo aur memory variables lock karo
    load_sariqx_config()
    
    # Step 2: Lazy loading factories ko pull karo compilation loop bypass karne ke liye
    from app.db.postgres import get_async_engine
    from app.db.mongo import mongo_manager
    from app.models.auth import Base 
    
    engine = get_async_engine() # Resolves the singleton instance post-config pre-warming
    
    # === RELATIONAL BOUNDARY (POSTGRES ENGINE) ===
    logger.info("Warming up PostgreSQL Async Connection Pool...")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        # Transaction context open karke physical tables schema inject karna
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✅ PostgreSQL Async Connection Pool pre-warmed & Master Schemas verified.")
    except Exception as e:
        logger.exception(f"💥 PostgreSQL initialization crashed: {e}")
        traceback.print_exc()
        raise SystemExit(1)
        
    # === DOCUMENT BOUNDARY (MONGO ENGINE) ===
    logger.info("Warming up MongoDB Motor Connection Pool...")
    try:
        mongo_manager.initialize_pool()
        await mongo_manager.client.admin.command('ping')
        logger.info("✅ MongoDB Async Authenticated Pool connection verified and warm.")
    except Exception as e:
        logger.exception(f"💥 MongoDB Secured Connection failed! Authentication error: {e}")
        traceback.print_exc()
        raise SystemExit(1) 
        
    yield  # SARIQX Engine starts routing active streams
    
    # 🏁 [SHUTDOWN ZONE]
    logger.info("Lifespan shutdown sequence initiated. Flushing assets...")
    try:
        await get_async_engine().dispose()
        logger.info("PostgreSQL connection pool disposed cleanly.")
        await mongo_manager.close_pool()
    except Exception as e:
        logger.exception(f"💥 Lifespan shutdown cleanup crashed: {e}")
        traceback.print_exc()
        raise
    finally:
        log_queue.put(None)
        logger_process.join()
        log_queue.close()
        log_queue.join_thread()
        print("🏁 SARIQX App Engine fully closed. Absolute Graceful Stop Achieved.")  
    

# 2. FastAPI Engine Core Instantiation
app = FastAPI(
    title="SARIQX Engine",
    description="Multi-Tenant High-Velocity Doubt Resolution SaaS Backend",
    version="1.0.0",
    lifespan=lifespan
)

# 🔄 Lazy loading of Middlewares after app initialization to prevent race conditions
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

# 🚀 Include System Auth Routers
from app.api.v1.auth import router as auth_router
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def root_ping():
    from loguru import logger
    try:
        logger.info("Ping endpoint hit - Testing block-free architecture pipeline")
        return {"status": "online", "engine": "SARIQX Hardened Core"}
    except Exception as e:
        logger.exception(f"💥 Root ping endpoint crashed: {e}")
        traceback.print_exc()
        raise
