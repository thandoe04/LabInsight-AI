# LabInsight AI — REST API Specification

Base URL: `/api/v1`

All responses return standard JSON. Authenticated requests require an active `labinsight_session` HttpOnly cookie. State-changing requests (`POST`, `PATCH`, `DELETE`) require the `X-CSRF-Token` header.

---

## 1. Authentication (`/auth`)

### `POST /auth/login`
- **Rate Limit**: 5 requests / minute
- **Body**: `{ "email": "admin@labinsight.dev", "password": "..." }`
- **Response** (`200 OK`): `{ "id": "...", "email": "...", "username": "...", "role": "administrator" }`
- **Cookies**: Sets `labinsight_session` (HttpOnly, SameSite=Strict).

### `POST /auth/logout`
- **Response** (`204 No Content`): Revokes session and clears cookie.

### `GET /auth/me`
- **Response** (`200 OK`): Returns current authenticated user profile.

---

## 2. Dashboard (`/dashboard`)

### `GET /dashboard/summary`
- **Response** (`200 OK`):
```json
{
  "total_patients": 5,
  "total_samples": 6,
  "total_tests": 6,
  "completed_tests": 5,
  "pending_tests": 1,
  "verified_results": 5,
  "data_quality_issues": 0,
  "statistical_anomalies": 1
}
```

### `GET /dashboard/charts`
- **Response** (`200 OK`): Sample status distributions and monthly activity trends.

### `GET /dashboard/activity`
- **Response** (`200 OK`): Chronological log of recent sample intake and result events.

---

## 3. Patients (`/patients`)

### `GET /patients`
- **Query Params**: `page`, `page_size`, `search`, `biological_sex`, `include_archived`
- **Response** (`200 OK`): Paginated patient records with pseudonymous codes.

### `POST /patients`
- **Body**: `{ "first_name": "Alex", "last_name": "Taylor", "date_of_birth": "1985-04-12", "biological_sex": "female", "is_synthetic": true }`
- **Response** (`201 Created`): Created patient profile.

### `GET /patients/{id}/history`
- **Response** (`200 OK`): Complete timeline of specimens and test results for the patient.

---

## 4. Samples (`/samples`)

### `GET /samples`
- **Query Params**: `page`, `page_size`, `status`, `sample_type`, `search`

### `POST /samples`
- **Body**: `{ "patient_id": "...", "sample_type": "whole_blood", "collection_notes": "Fasting sample" }`
- **Response** (`201 Created`): Generates unique code `SMP-YYYY-XXXXXX`.

### `PATCH /samples/{id}/status`
- **Body**: `{ "new_status": "received", "notes": "Cold chain verified" }`
- **Validation**: Enforces state transition machine (`registered` &rarr; `collected` &rarr; `received` &rarr; `processing` &rarr; `completed` / `rejected`).

### `GET /samples/{id}/history`
- **Response** (`200 OK`): Chain of custody history entries with timestamps and operators.

---

## 5. Laboratory Assays (`/laboratory`)

### `GET /laboratory/tests`
- **Response** (`200 OK`): Test catalogue with configured reference intervals.

### `POST /laboratory/tests`
- **Body**: `{ "test_code": "TSH", "name": "Thyroid Stimulating Hormone", "category_id": "...", "measurement_unit": "uIU/mL" }`

### `POST /laboratory/reference-ranges`
- **Body**: `{ "test_id": "...", "lower_limit": 0.4, "upper_limit": 4.0, "source": "CLSI Guideline 2026" }`

---

## 6. Test Results (`/results`)

### `GET /results`
- **Query Params**: `sample_id`, `test_id`, `status`

### `POST /results`
- **Body**: `{ "sample_id": "...", "test_id": "...", "numeric_value": 14.2 }`
- **Automatic Flagging**: Compares with active reference range and sets `is_above_upper_limit` / `is_below_lower_limit`.

### `POST /results/{id}/verify`
- **Response** (`200 OK`): Locks result into `verified` status.

### `PATCH /results/{id}/revise`
- **Body**: `{ "new_numeric_value": 15.0, "reason": "Sample re-run on dilution" }`
- **Audit**: Creates immutable `ResultRevision` record preserving old and new values.

---

## 7. Machine Learning & Quality (`/ml`)

### `POST /ml/experiments`
- **Body**: `{ "name": "Anomaly Run 1", "experiment_type": "anomaly_detection", "algorithm": "isolation_forest" }`

### `POST /ml/experiments/{id}/run`
- **Response** (`200 OK`): Executes model pipeline and generates anomaly records or PCA clusters.

### `GET /ml/anomalies`
- **Response** (`200 OK`): List of detected multivariate outliers with anomaly scores and contributing features.

### `PATCH /ml/anomalies/{id}/review`
- **Body**: `{ "review_status": "reviewed", "reviewer_notes": "Biological normal variant" }`

---

## 8. Reports (`/reports`)

### `POST /reports`
- **Body**: `{ "title": "Quarterly Summary", "report_type": "results", "format": "pdf" }`

### `GET /reports/{id}/download`
- **Response**: Binary file stream (`application/pdf`, `text/csv`, or `.xlsx`) with formula injection defense.
