# LabInsight AI

**Healthcare Laboratory Data Analytics and Machine Learning Platform**

> ⚠️ **Clinical Safety Notice**: LabInsight AI is a laboratory administration, research, and statistical analytics platform. It is **not** a medical diagnostic system and must never be used to diagnose diseases, recommend treatments, or make independent clinical decisions. All statistical anomalies and machine learning findings require review by qualified laboratory professionals.

---

## Overview

LabInsight AI is a secure, full-stack web application that enables authorised laboratory personnel, data analysts, and researchers to:

- Manage laboratory records (patients, samples, tests, results)
- Monitor operational activity through real-time dashboards
- Perform statistical analytics on historical laboratory data
- Detect statistical anomalies using machine learning
- Discover data patterns through unsupervised clustering
- Assess data quality using intelligent validation
- Generate compliant reports
- Maintain complete audit trails

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript 5, Vite 6, Tailwind CSS 3 |
| State Management | TanStack Query v5, React Hook Form |
| Backend | Python 3.13, FastAPI 0.115, Pydantic v2 |
| Database | PostgreSQL 16, SQLAlchemy 2.0, Alembic |
| Cache / Sessions | Redis 7 |
| Machine Learning | Scikit-learn 1.6, PyTorch 2.5, MLflow 2.18 |
| Infrastructure | Docker, Docker Compose |
| Security | Argon2id, TOTP MFA, HttpOnly session cookies, CSRF protection |

---

## Architecture

```
┌──────────────┐    HTTPS    ┌──────────────────────────┐
│   React SPA  │ ──────────▶ │   FastAPI Backend          │
│  (port 5173) │ ◀────────── │   (port 8000)              │
└──────────────┘             │                            │
                             │  ┌──────────────────────┐ │
                             │  │  ML Engine           │ │
                             │  │  Anomaly / Cluster   │ │
                             │  │  Data Quality        │ │
                             │  └──────────────────────┘ │
                             │                            │
                             └────────┬──────────────────┘
                                      │
                           ┌──────────┴──────────┐
                           │                     │
                    ┌──────▼──────┐    ┌─────────▼──────┐
                    │ PostgreSQL  │    │     Redis       │
                    │  (port 5432)│    │  (port 6379)    │
                    └─────────────┘    └────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker Desktop (with Docker Compose v2)
- Git

### 1. Clone the repository

```bash
git clone <repository-url> LabInsight-AI
cd LabInsight-AI
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` and set a strong `SECRET_KEY` and database credentials.

### 3. Start all services

```bash
docker compose up --build
```

### 4. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5. Seed development data

```bash
docker compose exec backend python -m app.db.seed
```

### 6. Access the application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MLflow UI | http://localhost:5000 |

### Demo Accounts (development only)

| Role | Email | Password |
|------|-------|----------|
| Administrator | admin@labinsight.dev | DevAdmin@2026! |
| Technician | tech@labinsight.dev | DevTech@2026! |
| Analyst | analyst@labinsight.dev | DevAnalyst@2026! |
| Researcher | researcher@labinsight.dev | DevResearch@2026! |

> ⚠️ **Development credentials only.** Never use these in production.

---

## Running Tests

### Backend tests

```bash
docker compose exec backend pytest tests/ -v --cov=app
```

### Frontend tests

```bash
docker compose exec frontend npm run test
```

### End-to-end tests

```bash
docker compose exec frontend npx playwright test
```

### Security analysis

```bash
docker compose exec backend bandit -r app/ -f json -o /tmp/bandit-report.json
docker compose exec backend pip-audit
```

---

## Project Structure

```
LabInsight-AI/
├── frontend/          # React + TypeScript SPA
├── backend/           # FastAPI Python application
│   ├── app/
│   │   ├── api/       # HTTP route handlers
│   │   ├── core/      # Config, security settings
│   │   ├── db/        # Database session, base model
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── schemas/   # Pydantic request/response schemas
│   │   ├── services/  # Business logic
│   │   ├── repositories/ # Database access layer
│   │   ├── security/  # Auth, sessions, CSRF, MFA
│   │   ├── ml/        # Machine learning engine
│   │   └── reporting/ # Report generation
│   └── alembic/       # Database migrations
├── database/          # DB documentation and ERD
├── infrastructure/    # Docker and deployment configs
├── docs/              # Architecture and user docs
├── docker-compose.yml
└── SECURITY.md
```

---

## Documentation

- [Architecture](docs/architecture.md)
- [Database Design](docs/database-design.md)
- [API Documentation](docs/api-documentation.md)
- [Security Architecture](docs/security-architecture.md)
- [Machine Learning](docs/ml-documentation.md)
- [User Manual](docs/user-manual.md)

---

## Security

Please read [SECURITY.md](SECURITY.md) for the security policy, vulnerability reporting procedure, and known limitations.

---

## License

This project is developed as a portfolio demonstration. Consult appropriate legal counsel before any clinical or production deployment.
