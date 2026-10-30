"""
SQLAlchemy ORM models package.
All models imported here so Alembic autogenerate can discover them.
"""
from app.models.user import (
    User, Role, Permission, RolePermission,
    UserSession, MFACredential, PasswordResetToken, LoginEvent,
)
from app.models.patient import Patient
from app.models.laboratory import TestCategory, LaboratoryTest, ReferenceRange
from app.models.sample import Sample, SampleStatusHistory
from app.models.result import TestResult, ResultRevision, ResultVerification
from app.models.ml import (
    Dataset, DatasetVersion, MLModel, MLModelVersion,
    MLExperiment, MLPrediction, AnomalyRecord, DataQualityIssue,
)
from app.models.audit import AuditLog
from app.models.system import Notification, SystemSetting, Report

__all__ = [
    "User", "Role", "Permission", "RolePermission",
    "UserSession", "MFACredential", "PasswordResetToken", "LoginEvent",
    "Patient",
    "TestCategory", "LaboratoryTest", "ReferenceRange",
    "Sample", "SampleStatusHistory",
    "TestResult", "ResultRevision", "ResultVerification",
    "Dataset", "DatasetVersion", "MLModel", "MLModelVersion",
    "MLExperiment", "MLPrediction", "AnomalyRecord", "DataQualityIssue",
    "AuditLog",
    "Notification", "SystemSetting", "Report",
]
