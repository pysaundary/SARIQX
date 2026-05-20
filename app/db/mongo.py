from motor.motor_asyncio import AsyncIOMotorClient
from app.core.collector import collector
from loguru import logger

class SARIQXMongoManager:
    """
    MongoDB Async Connection Pool Manager using Motor.
    Centralized instance control to manage non-blocking database queries.
    """
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None

    def initialize_pool(self) -> None:
        """
        Pydantic settings se credentials utha kar background connection pools open karna.
        """
        mongo_url = collector.get("MONGO_URL")
        main_db_name = collector.get("MONGO_MAIN_DB", "sariqx_system_db")

        if not mongo_url:
            logger.critical("❌ MONGO_URL lookup failed in ObjectCollector matrix!")
            raise RuntimeError("MongoDB connection configurations missing.")

        logger.info("🍃 Initializing SARIQX MongoDB Async Pool (Motor Client)...")
        
        try:
            # Create the Async Client Engine with optimized connection pool configuration
            self.client = AsyncIOMotorClient(
                mongo_url,
                maxPoolSize=50,             # High-throughput analytics ke liye 50 concurrent operations allowed hain
                minPoolSize=10,             # 10 connections hamesha pre-warmed background mein ready rahenge
                serverSelectionTimeoutMS=5000, # Agar database 5 sec tak respond na kare toh timeout throw karo
                uuidRepresentation="standard" # UUID compatibility strictly set to standard for python drivers
            )
            
            # Select the main primary database mapping context
            self.db = self.client[main_db_name]
            logger.info(f"💾 MongoDB Engine bound successfully to core workspace: '{main_db_name}'")
            
        except Exception as e:
            logger.opt(exception=True).critical(f"💥 Failed to instantiate Motor Client connection state: {e}")
            raise

    async def close_pool(self) -> None:
        """Shutdown par connections ko gracefully release karne ke liye."""
        if self.client:
            logger.info("♻️ Disposing SARIQX MongoDB non-blocking client connection pool...")
            self.client.close()
            logger.info("🍃 MongoDB pool disconnected cleanly.")


# Global exportable manager blueprint object
mongo_manager = SARIQXMongoManager()

# FastAPI Dynamic Dependency Injector for Endpoints
async def get_mongodb():
    """
    Returns the active database instance layer context per API request.
    """
    if mongo_manager.db is None:
        logger.error("🚫 Attempted to access MongoDB instance before warmup cycle execution.")
        raise RuntimeError("MongoDB client state engine is offline.")
    return mongo_manager.db
