"""
Seed data script for LabInsight AI development environment.
Creates demo roles, permissions, accounts, test catalogue, reference ranges,
and synthetic patient/sample/result records.

NEVER run or use these credentials in a production environment.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.audit import AuditLog
from app.models.laboratory import LaboratoryTest, ReferenceRange, TestCategory
from app.models.patient import Patient
from app.models.result import TestResult
from app.models.sample import Sample, SampleStatusHistory
from app.models.user import Permission, Role, RolePermission, User
from app.security.password import hash_password


async def seed_data():
    """Execute the database seed sequence."""
    async with engine.begin() as conn:
        # Create all schema tables directly for local dev
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        existing_role = await session.execute(select(Role).where(Role.name == "administrator"))
        if existing_role.scalar_one_or_none():
            print("Database already contains seed data. Skipping.")
            return

        print("Seeding roles and permissions...")
        # 1. Roles
        admin_role = Role(name="administrator", display_name="Administrator", is_system_role=True)
        tech_role = Role(name="technician", display_name="Laboratory Technician", is_system_role=True)
        analyst_role = Role(name="analyst", display_name="Data Analyst", is_system_role=True)
        researcher_role = Role(name="researcher", display_name="Clinical Researcher", is_system_role=True)

        session.add_all([admin_role, tech_role, analyst_role, researcher_role])
        await session.flush()

        # Permissions
        super_perm = Permission(name="all", resource="*", action="*", description="Full system access")
        session.add(super_perm)
        await session.flush()

        session.add(RolePermission(role_id=admin_role.id, permission_id=super_perm.id))

        print("Seeding demo user accounts...")
        # 2. Users (Argon2id passwords)
        users = [
            User(
                email="admin@labinsight.dev",
                username="admin",
                full_name="Dr. Sarah Chen, Ph.D.",
                password_hash=hash_password("DevAdmin@2026!"),
                role_id=admin_role.id,
                is_active=True,
            ),
            User(
                email="tech@labinsight.dev",
                username="technician",
                full_name="Marcus Vance, MLS",
                password_hash=hash_password("DevTech@2026!"),
                role_id=tech_role.id,
                is_active=True,
            ),
            User(
                email="analyst@labinsight.dev",
                username="analyst",
                full_name="Elena Rostova, M.Sc.",
                password_hash=hash_password("DevAnalyst@2026!"),
                role_id=analyst_role.id,
                is_active=True,
            ),
            User(
                email="researcher@labinsight.dev",
                username="researcher",
                full_name="Dr. Julian Thorne, MD",
                password_hash=hash_password("DevResearch@2026!"),
                role_id=researcher_role.id,
                is_active=True,
            ),
        ]
        session.add_all(users)
        await session.flush()
        admin_user = users[0]

        print("Seeding test categories and catalogue...")
        # 3. Test Categories
        cat_haem = TestCategory(name="Haematology", description="Complete blood counts, morphology, and coagulation.")
        cat_bio = TestCategory(name="Biochemistry", description="Electrolytes, liver/kidney profiles, lipid panels.")
        cat_imm = TestCategory(name="Immunology", description="Antibodies, immunoglobulins, and autoimmune markers.")
        session.add_all([cat_haem, cat_bio, cat_imm])
        await session.flush()

        # 4. Tests
        tests = [
            LaboratoryTest(
                test_code="HB",
                name="Hemoglobin",
                category_id=cat_haem.id,
                measurement_unit="g/dL",
                result_type="numeric",
                description="Oxygen-carrying protein in red blood cells.",
                created_by_id=admin_user.id,
            ),
            LaboratoryTest(
                test_code="WBC",
                name="White Blood Cell Count",
                category_id=cat_haem.id,
                measurement_unit="10^3/uL",
                result_type="numeric",
                description="Total leukocyte count in peripheral blood.",
                created_by_id=admin_user.id,
            ),
            LaboratoryTest(
                test_code="GLU",
                name="Fasting Blood Glucose",
                category_id=cat_bio.id,
                measurement_unit="mg/dL",
                result_type="numeric",
                description="Serum glucose level after overnight fasting.",
                created_by_id=admin_user.id,
            ),
            LaboratoryTest(
                test_code="CHOL",
                name="Total Cholesterol",
                category_id=cat_bio.id,
                measurement_unit="mg/dL",
                result_type="numeric",
                description="Circulating total serum cholesterol.",
                created_by_id=admin_user.id,
            ),
            LaboratoryTest(
                test_code="CREAT",
                name="Creatinine",
                category_id=cat_bio.id,
                measurement_unit="mg/dL",
                result_type="numeric",
                description="Renal function filtration marker.",
                created_by_id=admin_user.id,
            ),
            LaboratoryTest(
                test_code="ALT",
                name="Alanine Aminotransferase",
                category_id=cat_bio.id,
                measurement_unit="U/L",
                result_type="numeric",
                description="Enzyme concentrated in hepatic tissue.",
                created_by_id=admin_user.id,
            ),
        ]
        session.add_all(tests)
        await session.flush()

        print("Seeding documented demonstration reference intervals...")
        # 5. Reference Intervals (clearly marked as demonstration/guideline-based)
        ref_ranges = [
            ReferenceRange(
                test_id=tests[0].id,  # HB
                applicable_sex="all",
                lower_limit=12.0,
                upper_limit=17.5,
                unit="g/dL",
                source="WHO Hemoglobin Concentrations Guidelines (Demo Dataset)",
                authorised_by_id=admin_user.id,
            ),
            ReferenceRange(
                test_id=tests[1].id,  # WBC
                applicable_sex="all",
                lower_limit=4.5,
                upper_limit=11.0,
                unit="10^3/uL",
                source="Standard Clinical Pathology Reference (Demo Dataset)",
                authorised_by_id=admin_user.id,
            ),
            ReferenceRange(
                test_id=tests[2].id,  # GLU
                applicable_sex="all",
                lower_limit=70.0,
                upper_limit=99.0,
                unit="mg/dL",
                source="American Diabetes Association Fasting Guidelines (Demo Dataset)",
                authorised_by_id=admin_user.id,
            ),
            ReferenceRange(
                test_id=tests[3].id,  # CHOL
                applicable_sex="all",
                lower_limit=125.0,
                upper_limit=200.0,
                unit="mg/dL",
                source="NCEP ATP III Reference (Demo Dataset)",
                authorised_by_id=admin_user.id,
            ),
            ReferenceRange(
                test_id=tests[4].id,  # CREAT
                applicable_sex="all",
                lower_limit=0.6,
                upper_limit=1.3,
                unit="mg/dL",
                source="KDIGO Clinical Practice Guideline (Demo Dataset)",
                authorised_by_id=admin_user.id,
            ),
            ReferenceRange(
                test_id=tests[5].id,  # ALT
                applicable_sex="all",
                lower_limit=7.0,
                upper_limit=56.0,
                unit="U/L",
                source="ACR Laboratory Reference (Demo Dataset)",
                authorised_by_id=admin_user.id,
            ),
        ]
        session.add_all(ref_ranges)
        await session.flush()

        print("Seeding synthetic patient records...")
        # 6. Synthetic Patients
        patients = [
            Patient(
                patient_code="PAT-SYN-8812",
                first_name="Alex",
                last_name="Taylor",
                date_of_birth=date(1985, 4, 12),
                biological_sex="female",
                is_synthetic=True,
                created_by_id=admin_user.id,
            ),
            Patient(
                patient_code="PAT-SYN-9144",
                first_name="Jordan",
                last_name="Kim",
                date_of_birth=date(1978, 11, 23),
                biological_sex="male",
                is_synthetic=True,
                created_by_id=admin_user.id,
            ),
            Patient(
                patient_code="PAT-SYN-7021",
                first_name="Morgan",
                last_name="Patel",
                date_of_birth=date(1992, 8, 5),
                biological_sex="female",
                is_synthetic=True,
                created_by_id=admin_user.id,
            ),
            Patient(
                patient_code="PAT-SYN-4309",
                first_name="Casey",
                last_name="Mwamba",
                date_of_birth=date(1964, 2, 19),
                biological_sex="male",
                is_synthetic=True,
                created_by_id=admin_user.id,
            ),
            Patient(
                patient_code="PAT-SYN-6615",
                first_name="Riley",
                last_name="O'Connor",
                date_of_birth=date(2001, 7, 30),
                biological_sex="not_specified",
                is_synthetic=True,
                created_by_id=admin_user.id,
            ),
        ]
        session.add_all(patients)
        await session.flush()

        print("Seeding synthetic samples and test results...")
        # 7. Samples & Results
        now = datetime.now(timezone.utc)
        sample_types = ["serum", "whole_blood", "plasma"]
        
        sample_data = [
            ("SMP-2026-A101", patients[0], "whole_blood", "completed", [(tests[0], 13.8), (tests[1], 6.2)]),
            ("SMP-2026-B202", patients[1], "serum", "completed", [(tests[2], 142.0), (tests[3], 245.0)]),  # High Glucose & Chol
            ("SMP-2026-C303", patients[2], "serum", "completed", [(tests[4], 0.9), (tests[5], 28.0)]),
            ("SMP-2026-D404", patients[3], "whole_blood", "completed", [(tests[0], 9.8), (tests[1], 14.5)]),  # Low HB, High WBC
            ("SMP-2026-E505", patients[4], "serum", "processing", [(tests[2], 88.0)]),
            ("SMP-2026-F606", patients[0], "serum", "received", []),
        ]

        for s_code, pat, s_type, status_val, test_vals in sample_data:
            coll_dt = now - timedelta(days=5, hours=2)
            recv_dt = now - timedelta(days=5)
            s = Sample(
                sample_code=s_code,
                patient_id=pat.id,
                sample_type=s_type,
                status=status_val,
                collected_at=coll_dt,
                received_at=recv_dt,
                registered_by_id=admin_user.id,
            )
            session.add(s)
            await session.flush()

            session.add(
                SampleStatusHistory(
                    sample_id=s.id,
                    previous_status=None,
                    new_status=status_val,
                    changed_by_id=admin_user.id,
                    notes="Synthetic seed transition",
                )
            )

            for t_def, num_val in test_vals:
                # Determine flags
                is_above = False
                is_below = False
                if t_def.test_code == "HB":
                    is_below = num_val < 12.0
                elif t_def.test_code == "WBC":
                    is_above = num_val > 11.0
                elif t_def.test_code == "GLU":
                    is_above = num_val > 99.0
                elif t_def.test_code == "CHOL":
                    is_above = num_val > 200.0

                tr = TestResult(
                    sample_id=s.id,
                    test_id=t_def.id,
                    numeric_value=num_val,
                    measurement_unit=t_def.measurement_unit,
                    is_above_upper_limit=is_above,
                    is_below_lower_limit=is_below,
                    measured_at=recv_dt + timedelta(hours=3),
                    status="verified" if status_val == "completed" else "pending",
                    recorded_by_id=admin_user.id,
                )
                session.add(tr)

        # 8. Initial audit event
        session.add(
            AuditLog(
                actor_id=admin_user.id,
                actor_username="system_seed",
                action="system.seed",
                outcome="success",
                entity_type="system",
                metadata_={"message": "Initial development seed data loaded successfully."},
            )
        )

        await session.commit()
        print("Database seed successfully completed!")


if __name__ == "__main__":
    asyncio.run(seed_data())
