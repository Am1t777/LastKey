# LastKey — Digital Inheritance Vault

## Context
Building a portfolio project for junior software engineering interviews. LastKey is a secure digital inheritance vault — users store encrypted secrets (passwords, documents, notes) that get released to designated beneficiaries after the user's death/incapacitation, verified by a trusted verifier. The project demonstrates cryptography, system design, security best practices, and real problem-solving.

## Tech Stack
- **Backend:** Python + FastAPI (modern, async, auto-docs at `/docs`)
- **Frontend:** React (minimal, clean dashboard)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Encryption:** `cryptography` Python library (AES-256-GCM + Argon2 key derivation)
- **Auth:** JWT tokens with bcrypt password hashing
- **Background jobs:** APScheduler (for check-in cron jobs)
- **Email:** SMTP (or SendGrid free tier for demo)

## Architecture Overview

```
React Frontend  <-->  FastAPI Backend  <-->  PostgreSQL
                           |
                      APScheduler
                      (check-in cron)
                           |
                      Email Service
                      (notifications)
```

## Database Models

### User
- id, email, password_hash, name, created_at
- check_in_interval_days (default 30)
- last_check_in_at
- is_active

### TrustedVerifier
- id, user_id (FK), name, email, verification_token
- has_confirmed (boolean)
- confirmed_at

### Beneficiary
- id, user_id (FK), name, email
- public_key (for encrypting their access key)

### Secret
- id, user_id (FK), title, encrypted_content, encryption_iv, encryption_tag
- secret_type (enum: password, note, document, file)
- created_at, updated_at

### SecretAssignment
- id, secret_id (FK), beneficiary_id (FK)
- encrypted_key (secret's key encrypted with beneficiary's public key)

### AuditLog
- id, user_id, action, details, ip_address, created_at

## Encryption Design

1. **User registers** → password hashed with bcrypt for auth
2. **User creates a secret** → random AES-256 key generated → content encrypted with AES-256-GCM → key encrypted with each assigned beneficiary's public key → stored in SecretAssignment
3. **Secret release** → beneficiary authenticates → gets their encrypted key → decrypts with their private key → decrypts the secret content
4. **Zero-knowledge** → server never stores plaintext secrets or unencrypted keys

## Dead Man's Switch Flow

```
1. User sets check_in_interval (e.g., 30 days)
2. APScheduler runs daily cron job:
   - Find users where (now - last_check_in) > check_in_interval
   - Send reminder email with one-click check-in link
3. If no check-in after reminder + 7 day grace period:
   - Contact Trusted Verifier via email
   - Verifier clicks "Confirm" or "They're fine"
4. If verifier confirms → notify beneficiaries
5. Beneficiaries verify identity → receive their secrets
6. If verifier says "they're fine" → reset countdown, notify user
```

## Security Features (interview talking points)
- **SQL injection proof:** SQLAlchemy ORM with parameterized queries (never raw SQL)
- **XSS protection:** React escapes by default + Content-Security-Policy headers
- **CSRF protection:** JWT in httpOnly cookies + CSRF tokens
- **Man-in-the-middle:** HTTPS enforcement, HSTS headers
- **Rate limiting:** slowapi on all endpoints (brute-force protection)
- **Input validation:** Pydantic models validate every request
- **Audit logging:** every sensitive action logged with IP + timestamp
- **Zero-knowledge encryption:** server never sees plaintext secrets

---

## Implementation Plan

### Step 1: Project Setup
- Initialize project structure:
  ```
  lastkey/
  ├── backend/
  │   ├── app/
  │   │   ├── main.py          (FastAPI app, CORS, middleware)
  │   │   ├── config.py        (settings, env vars)
  │   │   ├── database.py      (SQLAlchemy engine + session)
  │   │   ├── models/          (SQLAlchemy models)
  │   │   ├── schemas/         (Pydantic request/response schemas)
  │   │   ├── routers/         (API endpoints)
  │   │   ├── services/        (business logic + encryption)
  │   │   ├── middleware/       (rate limiting, CSRF, auth)
  │   │   └── utils/           (email, helpers)
  │   ├── requirements.txt
  │   └── .env
  ├── frontend/
  │   ├── src/
  │   │   ├── components/
  │   │   ├── pages/
  │   │   ├── services/        (API calls)
  │   │   └── App.jsx
  │   └── package.json
  └── README.md
  ```
- Set up PostgreSQL database
- Set up FastAPI with CORS, middleware, error handling
- Set up SQLAlchemy + Alembic migrations

### Step 2: Database Models + Migrations
- Create all SQLAlchemy models (User, TrustedVerifier, Beneficiary, Secret, SecretAssignment, AuditLog)
- Create Alembic migration
- Test DB connection and table creation

### Step 3: Authentication System
- POST `/api/auth/register` — register with email + password (bcrypt hash)
- POST `/api/auth/login` — returns JWT token
- POST `/api/auth/logout` — invalidate token
- GET `/api/auth/me` — get current user
- Middleware: JWT verification on protected routes
- Rate limiting on auth endpoints (5 attempts per minute)

### Step 4: Encryption Service
- `generate_secret_key()` — random AES-256 key
- `encrypt_content(plaintext, key)` — AES-256-GCM encryption, returns (ciphertext, iv, tag)
- `decrypt_content(ciphertext, key, iv, tag)` — AES-256-GCM decryption
- `derive_key(password, salt)` — Argon2id key derivation
- `generate_keypair()` — RSA-2048 keypair for beneficiaries
- `encrypt_key_for_beneficiary(secret_key, public_key)` — RSA-OAEP
- `decrypt_key_as_beneficiary(encrypted_key, private_key)` — RSA-OAEP

### Step 5: Secrets Management API
- POST `/api/secrets` — create encrypted secret (encrypt on server with user's derived key)
- GET `/api/secrets` — list user's secrets (titles only, not decrypted)
- GET `/api/secrets/{id}` — get + decrypt a specific secret
- PUT `/api/secrets/{id}` — update a secret
- DELETE `/api/secrets/{id}` — delete a secret
- All endpoints log to AuditLog

### Step 6: Beneficiary Management API
- POST `/api/beneficiaries` — add beneficiary (name, email)
- GET `/api/beneficiaries` — list beneficiaries
- DELETE `/api/beneficiaries/{id}` — remove beneficiary
- POST `/api/beneficiaries/{id}/assign/{secret_id}` — assign a secret to a beneficiary
- When assigned: secret's AES key is encrypted with beneficiary's public key

### Step 7: Trusted Verifier API
- POST `/api/verifier` — set trusted verifier (name, email)
- GET `/api/verifier` — get current verifier
- PUT `/api/verifier` — update verifier
- GET `/api/verify/{token}` — verifier confirmation page (public route)
- POST `/api/verify/{token}/confirm` — verifier confirms death
- POST `/api/verify/{token}/deny` — verifier denies (resets countdown)

### Step 8: Dead Man's Switch (Background Jobs)
- APScheduler cron job runs daily:
  - Check all users' last_check_in_at vs check_in_interval
  - Send reminder emails to overdue users
  - After grace period: contact trusted verifier
  - After verifier confirms: trigger secret release flow
- GET `/api/checkin` — one-click check-in endpoint (from email link)
- PUT `/api/settings/checkin-interval` — update check-in interval

### Step 9: Secret Release Flow
- When verifier confirms:
  1. Mark user account as "releasing"
  2. Email each beneficiary with a secure access link
  3. Beneficiary clicks link → verifies identity (email + code)
  4. Beneficiary receives their assigned secrets (decrypted with their private key)
  5. Log everything in AuditLog

### Step 10: Security Middleware
- Rate limiting (slowapi): all endpoints
- CORS: whitelist frontend origin only
- CSRF tokens on state-changing requests
- Security headers (HSTS, X-Content-Type-Options, X-Frame-Options, CSP)
- Input validation via Pydantic (already built into FastAPI)
- SQL injection: already handled by SQLAlchemy ORM

### Step 11: React Frontend
- Pages:
  - `/login` and `/register` — auth forms
  - `/dashboard` — overview (secrets count, beneficiaries, check-in status, next check-in date)
  - `/secrets` — list, create, edit, delete secrets
  - `/beneficiaries` — manage beneficiaries + assign secrets
  - `/verifier` — set up trusted verifier
  - `/settings` — check-in interval, account settings
  - `/access/{token}` — beneficiary access page (public)
  - `/verify/{token}` — verifier confirmation page (public)
- Minimal, clean design with a CSS framework (Tailwind or simple custom CSS)
- API service layer with axios + JWT interceptor

### Step 12: Testing + Polish
- Test the full flow end-to-end:
  1. Register → add secrets → add beneficiary → assign secrets → set verifier
  2. Simulate missed check-in → verifier gets email → confirms → beneficiary gets access
- Test security: try SQL injection, XSS, brute force login
- Add error handling and loading states in frontend
- Write a clear README with setup instructions and architecture diagram

## Verification Plan
1. Register a user, create secrets, add beneficiary, assign secrets, set verifier
2. Manually trigger the check-in cron job → verify reminder email sent
3. Skip check-in past grace period → verify verifier contacted
4. Click verifier confirm link → verify beneficiary notified
5. Open beneficiary access link → verify secrets are decrypted correctly
6. Try SQL injection in login form → verify it fails
7. Try brute force login → verify rate limiting kicks in
8. Check `/docs` page → verify all API endpoints are documented
