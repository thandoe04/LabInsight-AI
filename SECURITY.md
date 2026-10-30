# Security Policy — LabInsight AI

## Scope

LabInsight AI is a **laboratory administration, research, and statistical analytics platform**.

It is **not** a medical diagnostic system.

This document describes the security controls implemented, known limitations, and how to report vulnerabilities.

---

## Clinical Safety

**LabInsight AI must never be used to:**
- Diagnose diseases
- Recommend treatments or medication
- Make independent clinical decisions
- Replace qualified laboratory professionals

All machine learning outputs are statistical analyses only. Anomaly flags are not diagnostic findings. Any clinically significant finding must be reviewed and interpreted by qualified healthcare professionals.

---

## Security Controls

### Authentication
- Passwords hashed with Argon2id (memory-hard, tunable parameters)
- HttpOnly, Secure, SameSite=Strict session cookies
- No sensitive tokens stored in localStorage or sessionStorage
- CSRF protection on all state-changing requests
- Login rate limiting with progressive throttling
- TOTP-based multi-factor authentication for administrator accounts
- Session expiration and revocation
- Single-use, time-limited password reset tokens
- Login event auditing

### Authorisation
- Backend-enforced role-based access control (RBAC)
- Fine-grained permission system
- Deny-by-default
- Record-level access controls
- UUID primary keys to prevent sequential ID enumeration

### API Security
- Strict CORS allowlist (no wildcard with credentials)
- Pydantic request validation
- Request body size limits
- Rate limiting on all sensitive endpoints
- Safe error responses (no stack traces to clients)
- Security headers (CSP, HSTS, X-Content-Type-Options, etc.)
- API versioning

### Database Security
- Least-privilege runtime database account
- Parameterised queries via SQLAlchemy ORM
- PostgreSQL not exposed to public internet
- Foreign key, unique, and check constraints

### Machine Learning Security
- Dataset provenance tracking
- Model artifact checksums
- Controlled internal artifact registry
- No execution of arbitrary uploaded model files
- No loading of untrusted pickle/joblib artifacts

### Patient Data Privacy
- Synthetic data used for development
- Pseudonymous patient identifiers
- Data minimisation
- Access restricted by role and record-level controls
- Patient identifiers not included in URLs or log messages

---

## Known Limitations

- This application has **not been independently security-audited** for clinical deployment.
- MFA is implemented using TOTP; hardware token support (FIDO2/WebAuthn) is not yet included.
- Redis session store in single-node configuration is not highly available.
- Backup restoration procedures have not been externally tested in production.
- Container images are scanned during CI but no real-time runtime monitoring is included.
- OWASP ZAP scanning covers common vulnerabilities; a professional penetration test has not been performed.

---

## Reporting a Vulnerability

If you discover a security vulnerability:

1. **Do not** open a public GitHub issue.
2. Email details to the project maintainer at [MAINTAINER_EMAIL].
3. Include a description, reproduction steps, and potential impact.
4. Allow reasonable time for a fix before any public disclosure.

---

## Legal Notice

Before deploying this system with real patient data:

- Obtain qualified legal advice regarding applicable data protection laws.
- Assess compliance with applicable Zimbabwean Cyber and Data Protection legislation.
- Assess compliance with any applicable sector-specific health data regulations.
- Obtain appropriate data processing authorisation.
- Document all data processing purposes.
- Implement required data subject rights procedures.

---

## Security Updates

Dependencies should be reviewed regularly:

```bash
# Backend
pip-audit

# Frontend
npm audit

# Container images
docker scout cves labinsight-backend:latest
docker scout cves labinsight-frontend:latest
```
