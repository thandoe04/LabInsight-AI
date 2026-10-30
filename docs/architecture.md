# LabInsight AI — System Architecture Document

## 1. Executive Summary & Purpose

LabInsight AI is a full-stack, enterprise-grade healthcare laboratory data analytics, specimen management, and statistical machine learning platform. It empowers clinical laboratory managers, technicians, data analysts, and researchers to oversee laboratory operations, maintain an immutable chain of custody for biological specimens, detect multivariate statistical anomalies, cluster empirical test patterns, and audit operational data quality.

> ⚠️ **CRITICAL CLINICAL SAFETY NOTICE**  
> LabInsight AI is an administrative, statistical analytics, and research tool. It is **NOT** a medical diagnostic system, disease detection device, or automated clinical decision support system. Statistical anomalies, out-of-range reference interval flags, and machine learning cluster assignments do not constitute diagnoses or therapeutic guidelines. All diagnostic interpretations remain the strict responsibility of licensed healthcare personnel.

---

## 2. High-Level Architecture Topology

The platform is designed following a **modular monolith** paradigm with strict layer isolation, enabling independent horizontal scaling or microservice extraction:

```
┌────────────────────────────────────────────────────────┐
│               Client Web Layer (React SPA)             │
│   React 18 • TypeScript • Tailwind CSS • Recharts      │
└───────────────────────────┬────────────────────────────┘
                            │ HTTPS / REST (Port 8000)
                            ▼
┌────────────────────────────────────────────────────────┐
│               FastAPI Application Layer                │
│ ┌───────────────────┐  ┌─────────────────────────────┐ │
│ │ Security & Auth   │  │ Clinical Operations         │ │
│ │ Argon2id / Cookie │  │ Patients, Samples, Results  │ │
│ └───────────────────┘  └─────────────────────────────┘ │
│ ┌───────────────────┐  ┌─────────────────────────────┐ │
│ │ ML Engine         │  │ Reporting Service           │ │
│ │ IsoForest / LOF   │  │ PDF / CSV Formula Sanitizer │ │
│ └───────────────────┘  └─────────────────────────────┘ │
└───────────────────────────┬────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│   PostgreSQL 16 Engine    │ │   Redis 7 Cache Store    │
│ 29 Tables • Strict RLS    │ │ Rate Limiting & Sessions │
└───────────────────────────┘ └──────────────────────────┘
```

---

## 3. Component Responsibilities

### A. Frontend Layer (React 18 / TypeScript / Vite)
- **Role**: High-performance, accessible, responsive Single Page Application.
- **State Management**: TanStack Query v5 for server cache synchronization; React Context for authentication.
- **Security**: Double-submit CSRF header propagation, zero authentication tokens in `localStorage` or `sessionStorage`, defensive rendering against XSS.

### B. Backend Layer (Python 3.13 / FastAPI / Pydantic v2)
- **Role**: Async REST API handling business logic, validation, audit logging, and computational analytics.
- **Security**: Argon2id password hashing, HttpOnly `SameSite=Strict` opaque session cookies, request-level CSRF verification, rate limiting via SlowAPI.

### C. Relational Persistence Layer (PostgreSQL 16 / SQLAlchemy 2.0 / Alembic)
- **Role**: ACID-compliant transactional persistence across 29 normalized tables.
- **Integrity**: UUIDv4 primary keys (preventing IDOR enumeration), check constraints, foreign key cascades, append-only audit log tables.

### D. Machine Learning Engine (Scikit-Learn / SciPy / NumPy / PyTorch)
- **Role**: Unsupervised statistical pattern detection, dimensionality reduction, and rule-based data quality screening.
- **Isolation**: Controlled internal registry with SHA-256 artifact checksum verification; zero arbitrary user pickle loading.
