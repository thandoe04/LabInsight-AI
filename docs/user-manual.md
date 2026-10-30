# LabInsight AI — Operating User Manual

## 1. Getting Started & Role Privileges

LabInsight AI supports four clinical and research operational personas:

| Role | Operational Scope & Responsibilities |
|------|---------------------------------------|
| **Administrator** | User provisioning, test definition catalogue, reference interval management, system audit log inspection. |
| **Technician** | Specimen registration, lifecycle state advancement, test result entry, submission for verification. |
| **Analyst** | Statistical analytics, parametric evaluations, clustering runs, data quality issue review. |
| **Researcher** | Longitudinal time-series queries, ML experiment configuration, research data exports. |

---

## 2. Common Workflows

### A. Specimen Intake & Tracking
1. Navigate to **Samples** via the sidebar navigation.
2. Click **Intake Sample**.
3. Supply the pseudonymous patient code (e.g. `PAT-SYN-8812`) and select the specimen matrix type (`Whole Blood`, `Serum`, `Plasma`, `Urine`, `CSF`).
4. Click **Intake Specimen**. The system automatically generates a unique code (e.g. `SMP-2026-A101`).
5. As the specimen moves through laboratory stations, click **Advance** to transition status from `registered` &rarr; `collected` &rarr; `received` &rarr; `processing` &rarr; `completed`.

### B. Result Logging, Auto-Flagging & Revisions
1. Navigate to **Results & Revisions**.
2. Click **Enter Test Result**.
3. Select the target specimen and desired assay definition, then input the measured numeric value.
4. The system automatically cross-references active reference ranges and applies **HIGH**, **LOW**, or **NORMAL** tags.
5. Click **Verify** to confirm the result.
6. If an error is subsequently identified on a verified result, click **Revise**. Supply the corrected value and enter a **mandatory clinical audit reason**. The previous value is archived permanently in the revision log.

### C. Machine Learning & Anomaly Evaluation
1. Navigate to **ML & Data Quality**.
2. Under **Anomaly Detection**, click **Execute Anomaly Model**.
3. Review flagged outliers. Click **Review** on any anomaly record to register a formal evaluation decision (`Reviewed & Verified Normal Variation`, `Dismissed as Artifact`, or `Escalated for Laboratory Repeat Analysis`).
4. Switch to **Unsupervised Clustering** to project multi-dimensional assay results onto an interactive 2D PCA scatter chart.
5. Switch to **Data Quality Intelligence** and run a screening scan to surface any physiological impossibilities or timestamp contradictions.

### D. Report Exporting
1. Navigate to **Reports**.
2. Click **Generate Report**.
3. Select desired scope (`Test Results` or `Samples`) and format (`PDF`, `CSV`, or `Excel`).
4. Click **Download** on the compiled report row. All spreadsheet exports are actively sanitized against formula injection.
