# KESTRAL AI 🦅
### Enterprise Forensic Evidence Management & Video Surveillance Platform

Kestral AI is an enterprise-grade AI-powered CCTV and ATM video surveillance platform engineered with Clean Architecture, PostgreSQL, SQLAlchemy 2.0 typed ORM, Alembic migrations, PyJWT authentication, role-based access control (RBAC), and high-performance computer vision pipelines (YOLOv8 ByteTrack person tracking + OpenCV YuNet deep facial detection + Laplacian quality scoring).

---

## 🏗️ Architecture & Technology Stack

### Backend Architecture
- **Language**: Python 3.12+
- **Framework**: FastAPI (Asynchronous ASGI gateway)
- **Database**: PostgreSQL 16+ via SQLAlchemy 2.0 (Strict typed ORM, `Mapped`, `mapped_column`, UUID primary keys)
- **Schema Migrations**: Alembic (`alembic/versions/001_initial_schema.py`)
- **Data Validation & Serialisation**: Pydantic v2
- **Authentication**: JWT (PyJWT HS256) with Bcrypt password hashing
- **Authorization**: Granular Role-Based Access Control (Admin, Investigator, Officer, Analyst)
- **Containerization**: Docker & Docker Compose

### AI Vision Pipeline (Preserved & Integrated)
- **Person Detection & Tracking**: YOLOv8 ByteTrack multi-object tracking (`ultralytics`)
- **Facial Landmark Detection**: OpenCV YuNet ONNX Deep Neural Network (5-point facial landmarks)
- **Quality Assessment**: Laplacian sharpness variance, exposure, contrast, and resolution scoring
- **Forensic Evidence Selection**: Concurrency-safe atomic promotion of optimal candidate frame per track
- **Integrity Ledger**: Bitwise SHA-256 cryptographic hashing of raw videos and crop frames

### Frontend
- **Framework**: Next.js 16 (Turbopack) & React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4 & Radix UI
- **Networking**: Axios HTTP client

---

## 📁 Repository Structure

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
│   ├── tests/                        # Comprehensive Pytest Suite (18 tests)
│   ├── alembic.ini                   # Alembic configuration
│   ├── Dockerfile                    # Production container image
│   ├── main.py                       # Unified Application Entrypoint
│   └── requirements.txt              # Pinned dependencies
├── atm-vision-ai-dashboard/          # Next.js 16 + React 19 Frontend
├── docs/                             # Architecture & Sequence Documentation
│   ├── er-diagram.mmd
│   ├── database-relationships.mmd
│   ├── api-flow.mmd
│   ├── video-processing-sequence.mmd
│   └── folder-structure.md
├── docker-compose.yml                # Multi-container orchestration (Postgres + Backend + Frontend)
├── .dockerignore
└── README.md
```

---

## 🗄️ Database Architecture

The schema consists of 9 fully-typed PostgreSQL tables with UUID primary keys, timezone-aware UTC timestamps, foreign key relationships, and indexes:

| Table | Primary Key | Description |
|---|---|---|
| `users` | `id` (UUID) | System users with bcrypt password hash and role |
| `cameras` | `camera_id` (UUID) | Camera inventory with ATM ID, location, IP, status |
| `videos` | `video_id` (UUID) | Uploaded videos, duration, FPS, SHA-256, status |
| `person_tracks` | `track_id` (UUID) | Tracked individuals, frame ranges, best-evidence FK |
| `face_evidence` | `evidence_id` (UUID) | Crop and full frame paths, quality metrics, hashes |
| `investigation_cases` | `case_id` (UUID) | Case title, description, status, investigator FK |
| `case_evidence` | `(case_id, evidence_id)` | Composite primary key linking cases to evidence |
| `alerts` | `alert_id` (UUID) | Camera alerts with severity, message, ack timestamp |
| `audit_logs` | `log_id` (UUID) | Append-only non-repudiable audit ledger with JSONB |

### Forensic Rules Enforced
1. **At Most One Best Evidence Per Track**: Partial unique index on `face_evidence(track_id) WHERE is_best = true`.
2. **Atomic Promotion**: Candidate comparison executes inside row-locked transaction on `person_tracks` preventing concurrent race conditions.
3. **Evidence Preservation**: Prior candidate evidence records and files are never purged upon promotion.
4. **No Binary Blobs in PostgreSQL**: Database stores file paths and SHA-256 hashes only.

---

## 🔐 Role-Based Access Control (RBAC)

| Permission | Admin | Investigator | Officer | Analyst |
|---|:---:|:---:|:---:|:---:|
| User Management (`users:*`) | ✅ | ❌ | ❌ | ❌ |
| Camera Management (`cameras:*`) | ✅ | Read Only | Read Only | Read Only |
| Video Processing (`videos:*`) | ✅ | ✅ | Read Only | Read Only |
| Evidence Inspection (`evidence:read`) | ✅ | ✅ | ✅ | ✅ |
| Forensic Export (`evidence:export`) | ✅ | ✅ | ❌ | ✅ |
| Case Management (`cases:*`) | ✅ | ✅ | Read Only | Read Only |
| Alert Management (`alerts:*`) | ✅ | ✅ | ✅ | ❌ |
| Dashboard Metrics (`dashboard:stats`) | ✅ | ✅ | ✅ | ✅ |
| Audit Log Inspection (`audit:read`) | ✅ | ❌ | ❌ | ❌ |

---

## 🚀 Quick Start Guide

### Option 1: Docker Compose (Recommended)

1. Start all containers (PostgreSQL, FastAPI Backend, Next.js Frontend):
   ```bash
   docker compose up -d --build
   ```
2. Run database migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```
3. Access the services:
   - **Frontend Dashboard**: `http://localhost:3000`
   - **Backend API Docs**: `http://localhost:8000/docs`
   - **PostgreSQL**: `localhost:5432` (user: `postgres`, db: `kestral_db`)

---

### Option 2: Local Windows Development

#### 1. Database Setup
Ensure PostgreSQL 16+ is running and create the database:
```sql
CREATE DATABASE kestral_db;
```

#### 2. Backend Setup
```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run migrations
$env:PYTHONPATH="."
alembic upgrade head

# Start FastAPI Server
python main.py
```
Default administrator bootstrapped automatically:
- **Email**: `admin@kestral.ai`
- **Password**: `Admin123!SecurePassword`

#### 3. Frontend Setup
```powershell
cd atm-vision-ai-dashboard
npm install
npm run dev
```

---

## 🧪 Automated Testing

Run the full pytest suite (58 tests total: 18 architecture tests + 40 baseline tests):

```powershell
cd backend
$env:PYTHONPATH="."

# Run all clean architecture, auth, RBAC, promotion & export tests:
pytest -v tests/

# Run baseline AI pipeline and evaluation tests:
pytest -v test_pipeline.py test_evaluation.py test_camera.py
```

**Result**: 58/58 tests passing with 0 failures.
