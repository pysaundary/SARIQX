# SARIQX: Multi-Tenant Doubt-Solving Platform Engine
**Version:** 1.0 (Core Engine - High Performance Non-AI Phase)

## ⚡ High-Velocity Technical Framework
* **Package Management Engine:** `uv` (Rust-backed workspace resolution)
* **Asynchronous Event Loop Engine:** `uvloop` (Libuv interface bypassing native asyncio loop limits)
* **Core Application API Matrix:** FastAPI (Python Async runtime)
* **ACID Isolation Boundary:** PostgreSQL (Dynamic Schema-based Multi-Tenancy mapping)
* **High-Throughput Content Store:** MongoDB (Shared collection, strict tenant indexed documents)
* **Event Broker & Task Scheduler:** Celery distributed queues backed by Redis
* **I/O Overhead Minimization:** Custom IPC Multiprocessing Queue Daemon Logger

---

## 📁 System Blueprint Mapping

```text
sariqx_backend/
│
├── app/                       # Application boundary encapsulation
│   ├── api/                   # Ingestion points (Zero query logic allowed)
│   │   ├── v1/                
│   │   │   ├── tenant_admin.py # Institute schema and user pool administration
│   │   │   ├── student.py      # Main query submission and faceted search entry
│   │   │   └── superadmin.py   # Global metrics and client onboarding controller
│   │   └── dependencies.py     # Subdomain context grabber and active database session routing
│   │
│   ├── core/                  # Engine definitions
│   │   ├── config.py          # Environment structural checking via Pydantic settings
│   │   ├── security.py        # Asymmetric validation routines and tokens hashing
│   │   └── logger_client.py   # Atomic non-blocking queue ingestion wrapper
│   │
│   ├── db/                    # Connection connection instances
│   │   ├── postgres.py        # SQLAlchemy Async engine configuration
│   │   └── mongo.py           # Motor non-blocking database instances
│   │
│   ├── models/                # Relational data engines
│   │   ├── tenant.py          # Global public cluster mappings
│   │   └── user.py            # Isolated target schema users (Students, Mentors)
│   │
│   ├── schemas/               # Compile-time data validation definitions
│   │   ├── doubt.py           # Document schema constraints (MongoDB representations)
│   │   └── user.py            # API layer input/output verification contracts
│   │
│   ├── services/              # Pure business calculations layer
│   │   ├── tenant_service.py  # Run programmatic SQL schema scaffolding actions
│   │   └── doubt_service.py   # MongoDB multidimensional aggregate calculations ($facet pipeline compiler)
│   │
│   └── tasks/                 # Background event processes
│       ├── celery_app.py      # Core distribution logic management
│       └── sync_workers.py    # Eventual consistency pipeline mapping (Postgres state mutations -> MongoDB updates)
│
├── custom_logger/             # Separate system process space
│   └── logger_server.py       # Bound process draining communication pipeline queue directly to storage
│
├── .env.example               
├── docker-compose.yml         # Shared container composition config
└── main.py                    # Root setup script defining uvloop allocation rules