"""API v1 router aggregator."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, dashboard, patients, samples, laboratory, results, analytics, ml, reports, users, audit

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(patients.router, prefix="/patients", tags=["Patients"])
router.include_router(samples.router, prefix="/samples", tags=["Samples"])
router.include_router(laboratory.router, prefix="/laboratory", tags=["Laboratory"])
router.include_router(results.router, prefix="/results", tags=["Results"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(audit.router, prefix="/audit-logs", tags=["Audit"])
