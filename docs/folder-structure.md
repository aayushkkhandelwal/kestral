# Kestral AI Clean Architecture Folder Structure

```
kestral/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py               # Dependency injection (get_db, RBAC, JWT verification)
│   │   │   └── v1/
│   │   │       ├── alerts.py         # Alert management & acknowledgement endpoints
│   │   │       ├── auth.py           # Authentication, JWT login, logout, me
│   │   │       ├── cameras.py        # Camera inventory & CRUD operations
│   │   │       ├── cases.py          # Investigation case management & dossier exports
│   │   │       ├── dashboard.py      # Admin metrics & legacy stats endpoints
│   │   │       ├── evidence.py       # Evidence search, best-evidence, hash audit
│   │   │       ├── router.py         # V1 API router aggregation
│   │   │       ├── users.py          # User management with RBAC enforcement
│   │   │       └── videos.py         # Video upload, task tracking & results
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic v2 application settings & storage paths
│   │   │   ├── exceptions.py         # Typed domain exception hierarchy
│   │   │   ├── logging.py            # Structured logger configuration
│   │   │   ├── permissions.py        # UserRole enum & RBAC permission matrix
│   │   │   └── security.py           # Bcrypt password hashing & PyJWT token handling
│   │   ├── database/
│   │   │   ├── base.py               # DeclarativeBase SQLAlchemy 2.0
│   │   │   ├── init.py               # Database initialization & admin bootstrap
│   │   │   └── session.py            # Engine, sessionmaker & connection pool
│   │   ├── models/                   # SQLAlchemy 2.0 ORM Models
│   │   │   ├── __init__.py           # Model exports
│   │   │   ├── alert.py              # alerts table
│   │   │   ├── audit_log.py          # audit_logs table (JSONB / JSON)
│   │   │   ├── camera.py             # cameras table
│   │   │   ├── case_evidence.py      # case_evidence composite PK join table
│   │   │   ├── face_evidence.py      # face_evidence table with partial unique index
│   │   │   ├── investigation_case.py # investigation_cases table
│   │   │   ├── person_track.py       # person_tracks table
│   │   │   ├── user.py               # users table
│   │   │   └── video.py              # videos table
│   │   ├── repositories/             # Persistence Layer (SQLAlchemy 2.0)
│   │   │   ├── alert_repository.py
│   │   │   ├── audit_repository.py
│   │   │   ├── base.py
│   │   │   ├── camera_repository.py
│   │   │   ├── case_repository.py
│   │   │   ├── evidence_repository.py# Concurrency-safe best-evidence promotion
│   │   │   ├── track_repository.py
│   │   │   ├── user_repository.py
│   │   │   └── video_repository.py
│   │   ├── schemas/                  # Pydantic v2 DTOs
│   │   │   ├── alert.py
│   │   │   ├── auth.py
│   │   │   ├── camera.py
│   │   │   ├── case.py
│   │   │   ├── common.py             # PaginatedResponse[T]
│   │   │   ├── dashboard.py
│   │   │   ├── evidence.py
│   │   │   ├── person_track.py
│   │   │   ├── user.py
│   │   │   └── video.py
│   │   ├── services/                 # Domain Business Logic Layer
│   │   │   ├── alert_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── camera_service.py
│   │   │   ├── case_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── evidence_service.py
│   │   │   ├── export_service.py     # ZIP dossier export generator
│   │   │   ├── user_service.py
│   │   │   └── video_service.py
│   │   ├── middleware/
│   │   │   ├── rate_limit.py         # Request rate limiter
│   │   │   └── request_context.py    # Correlation ID (X-Request-ID) middleware
│   │   ├── utils/
│   │   │   ├── hashing.py            # SHA-256 chunked calculation
│   │   │   ├── pagination.py         # Bounded pagination helper
│   │   │   ├── storage.py            # Path-traversal safe disk storage manager
│   │   │   └── time.py               # Timezone-aware UTC helpers
│   │   └── ai/
│   │       └── adapters.py           # Clean adapter wrapping existing AI vision pipeline
│   ├── migrations/                   # Alembic Database Migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_schema.py # Complete 9-table schema migration
│   ├── services/                     # Preserved Core AI Vision Services
│   │   ├── best_frame.py             # Selection algorithm
│   │   ├── face_detector.py          # OpenCV YuNet 5-point facial landmarks
│   │   ├── face_quality.py           # Laplacian variance & exposure scoring
│   │   ├── identity_consolidator.py
│   │   ├── person_detector.py        # YOLOv8 ByteTrack person tracking
│   │   └── video_processor.py        # Multi-object video processing engine
│   ├── evaluation/                   # Dataset evaluation & metrics calculation
│   ├── uploads/                      # Raw video storage
│   ├── results/                      # Video task results & extracted frames
│   ├── faces/                        # Biometric face crop crops
│   ├── frames/                       # Full-resolution evidence frames
│   ├── exports/                      # Generated forensic ZIP dossiers
│   ├── tests/                        # Comprehensive Pytest Suite
│   ├── alembic.ini                   # Alembic configuration
│   ├── Dockerfile                    # Container definition
│   ├── main.py                       # Unified Application Entrypoint
│   └── requirements.txt              # Pinned dependencies
├── frontend/                         # Next.js 16 + React 19 Frontend
├── docs/                             # Architecture & Sequence Documentation
├── docker-compose.yml                # Multi-container orchestration (Postgres + Backend + Frontend)
├── .dockerignore
└── README.md                         # Complete project documentation
```
