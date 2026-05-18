#!/bin/bash

echo "⚡ Initializing SARIQX Architecture with Modern Python Blueprint..."

# 1. Initialize the project using the 'uv' package manager
if [ ! -f "pyproject.toml" ]; then
    echo "📦 Running 'uv init' to set up pyproject.toml..."
    uv init --app
else
    echo "📦 pyproject.toml already exists, skipping 'uv init'..."
fi

echo "📁 Generating scannable multi-tenant folder boundaries..."

# 2. Structural directory generation
mkdir -p app/api/v1
mkdir -p app/core
mkdir -p app/db
mkdir -p app/models
mkdir -p app/schemas
mkdir -p app/services
mkdir -p app/tasks
mkdir -p custom_logger

# 3. Injecting structural 'why.md' architecture files
echo "# Architectural Layer: App Boundary
SARIQX ka saara core application execution is folder mein encapsulated hai. Yeh external deployment processes se decoupled hai." > app/why.md

echo "# Architectural Layer: HTTP Ingestion
SARIQX routing logic layer. Yahan sirf HTTP methods (GET, POST, etc.) match hote hain. Business execution ya query compilation yahan strict prohibited hai." > app/api/why.md

echo "# Architectural Layer: API Versioning
Multi-client scalability ke liye APIs ko v1 par isolate kiya gaya hai taaki future deployment updates safe rahein." > app/api/v1/why.md

echo "# Architectural Layer: Systems Configuration & Core Essentials
SARIQX application ke state setups (Pydantic BaseSettings), asymmetric cryptographic utility, aur IPC multiprocessing logging client yahan exist karte hain." > app/core/why.md

echo "# Architectural Layer: Polyglot Database State Pools
PostgreSQL (SQLAlchemy Async engine) aur MongoDB (Motor Async client) dono ke connection states aur thread optimizations yahan handle hote hain." > app/db/why.md

echo "# Architectural Layer: Relational Schema Modeling
PostgreSQL strict tables blueprints (using SQLAlchemy 2.0 mapping). `tenant.py` contains public metrics; `user.py` maps isolated tenant nodes." > app/models/why.md

echo "# Architectural Layer: Data Interception & Structural Contracts
Pydantic V2 schemas compile-time type-safety check ke liye. Frontend se kya payload aayega aur kya return hoga, uski validation yahi se enforced hai." > app/schemas/why.md

echo "# Architectural Layer: Pure Business Logic Engine
SARIQX ka 'Asli Dimaag'. Complex Multi-tenant resolution schema triggers aur MongoDB `$facet` aggregation compilers completely is layer ke functional space mein rehte hain." > app/services/why.md

echo "# Architectural Layer: Asynchronous Job Queues
Celery workers framework. Data sync events (SQL se read-heavy Mongo nodes par sync push karna) aur long-running heavy tasks yahan execute hote hain." > app/tasks/why.md

echo "# Architectural Layer: Dead-Silent Zero I/O Logger Server
Independent operating system daemon process boundary. Main FastAPI process se data multiprocessing queue ke through receive karke physical execution (disk writes) handle karta hai." > custom_logger/why.md

# 4. Generating core module placeholders
touch main.py
touch .env.example
touch docker-compose.yml
touch custom_logger/logger_server.py
touch ARCHITECTURE.md

echo "⚡ Workspace directories compiled successfully."
echo "📥 Installing asynchronous runtime packages using 'uv' engine..."

# 5. Installing the high-velocity asynchronous tech stack using uv
uv add fastapi uvicorn uvloop pydantic pydantic-settings
uv add sqlalchemy asyncpg motor celery redis

echo "🚀 SARIQX Boilerplate Engine Setup Completed Successfully!"
echo "💡 To spin up the development environment with uvloop execution context, run:"
echo "   uv run uvicorn main:app --host 0.0.0.0 --port 8000 --loop uvloop --reload"