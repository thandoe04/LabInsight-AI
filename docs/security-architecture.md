# LabInsight AI — Security Architecture & Threat Model

## 1. Security Philosophy: Secure by Design & Privacy by Design

LabInsight AI implements defense-in-depth security principles across every architectural layer. Security controls are enforced at the backend level; frontend UI restrictions serve exclusively as ergonomic UX aids and are never treated as security boundaries.

---

## 2. Authentication & Credential Storage

### A. Argon2id Password Hashing
- Algorithm: `Argon2id` (memory-hard, resistant to GPU/ASIC brute-force cracking).
- Parameters: `m=65536` (64 MiB memory cost), `t=3` (3 iterations), `p=4` (4 parallel lanes).
- Automatic rehash detection upgrades stored hashes if parameters are adjusted in future releases.

### B. Opaque Server-Managed Sessions
- **No JWTs in localStorage**: Long-lived access tokens stored in browser local storage are vulnerable to Cross-Site Scripting (XSS).
- Sessions utilize cryptographically random 256-bit opaque tokens generated via Python `secrets.token_urlsafe(32)`.
- Storage: DB stores HMAC-SHA256 hashes of the token. The plaintext token is delivered solely in an `HttpOnly`, `SameSite=Strict`, `Secure` (production) cookie.
- Automatic revocation: User logout or security compromise immediately marks sessions as revoked.

### C. Double-Submit CSRF Protection
- For all state-changing HTTP verbs (`POST`, `PUT`, `PATCH`, `DELETE`), incoming requests must provide an `X-CSRF-Token` header that matches the authenticated `labinsight_csrf` cookie value.
- Timing-safe comparison using `secrets.compare_digest` prevents side-channel timing attacks.

---

## 3. Data Protection & Patient Privacy

### A. Synthetic Data Deployment
During development and evaluation, synthetic records are generated using pseudonymous identifiers (`PAT-SYN-XXXX`). Unnecessary personally identifiable information (PII) like national identity numbers or street addresses is strictly prohibited from collection.

### B. Pseudonymisation
All sample tracking and analytical jobs reference patients exclusively via their random pseudonymous code. Direct patient identifiers are never placed in URLs, query strings, or audit logs.

### C. Spreadsheet Formula Injection Defense (CWE-1236)
When exporting datasets to CSV or Excel (`openpyxl`), all cell values are screened. If a cell begins with formula execution characters (`=`, `+`, `-`, `@`, `\t`, `\r`), it is neutralized by prefixing a single quote `'`, preventing command execution in spreadsheet software.

---

## 4. Threat Matrix (STRIDE Model)

| Threat Category | Potential Attack Vector | Applied Countermeasure |
|-----------------|------------------------|------------------------|
| **Spoofing** | Credential stuffing on login | SlowAPI rate limiting (5 req/min), progressive lockouts, Argon2id |
| **Tampering** | Silent alteration of test results | Immutable `result_revisions` log, verified state locking, append-only `audit_logs` |
| **Repudiation** | User denies making a clinical revision | Mandatory audit reasoning, operator user ID capture, immutable timestamping |
| **Information Disclosure** | IDOR enumeration on records | UUIDv4 primary keys on all tables, backend role/record permission enforcement |
| **Denial of Service** | Volumetric spamming of ML endpoints | Per-IP rate limiting, body size limits, database query timeouts |
| **Elevation of Privilege** | User manipulates role payload | Strict Pydantic input schemas, deny-by-default role checks, server-side RBAC |
