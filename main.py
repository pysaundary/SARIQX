import multiprocessing
import uvloop
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text

# ⚡ Global High-Velocity Event Loop Installation
uvloop.install()

from app.core.logger_client import setup_app_logging_client
from custom_logger.logger_server import logger_worker_process

# 1. Daemon Logger Setup
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
    
    load_sariqx_config()
    
    from app.db.postgres import async_engine
    from app.db.mongo import mongo_manager
    # IMPORT BASE: Model registry ko memory mein maps karne ke liye forced import
    from app.models.auth import Base 
    
    # === RELATIONAL BOUNDARY (POSTGRES ENGINE) ===
    logger.info("Warming up PostgreSQL Async Connection Pool...")
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        # Transaction context open karke physical tables schema inject karna
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✅ PostgreSQL Async Connection Pool pre-warmed & Master Schemas verified.")
    except Exception as e:
        logger.critical(f"💥 PostgreSQL initialization crashed: {e}")
        raise SystemExit(1)
        
    # === DOCUMENT BOUNDARY (MONGO ENGINE) ===
    logger.info("Warming up MongoDB Motor Connection Pool...")
    try:
        mongo_manager.initialize_pool()
        await mongo_manager.client.admin.command('ping')
        logger.info("✅ MongoDB Async Authenticated Pool connection verified and warm.")
    except Exception as e:
        logger.critical(f"💥 MongoDB Secured Connection failed! Authentication error: {e}")
        raise SystemExit(1) 
        
    yield  # SARIQX Engine starts routing streams
    
    # 🏁 [SHUTDOWN ZONE]
    logger.info("Lifespan shutdown sequence initiated. Flushing assets...")
    await async_engine.dispose()
    logger.info("PostgreSQL connection pool disposed cleanly.")
    await mongo_manager.close_pool()
    
    log_queue.put(None)
    logger_process.join()
    log_queue.close()
    log_queue.join_thread()
    print("🏁 SARIQX App Engine fully closed. Absolute Graceful Stop Achieved.")  
    

# 2. FastAPI Engine Instantiation
app = FastAPI(
    title="SARIQX Engine",
    description="Multi-Tenant High-Velocity Doubt Resolution SaaS Backend",
    version="1.0.0",
    lifespan=lifespan
)

from app.core.collector import collector

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=collector.get("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
)

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