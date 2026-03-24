# LastKey — Digital Inheritance Vault

## Git Workflow
After every update or change, stage and push the changes to the git repository. Do not accumulate uncommitted work — commit and push promptly after each meaningful change.

## What is this?
A portfolio project for junior software engineering interviews. Users store encrypted secrets (passwords, documents, notes) that get released to designated beneficiaries after the user's death/incapacitation, verified by a trusted verifier ("dead man's switch").

## Tech Stack
- **Backend:** Python + FastAPI
- **Frontend:** React
- **Database:** PostgreSQL + SQLAlchemy ORM + Alembic migrations
- **Encryption:** `cryptography` library (AES-256-GCM + Argon2 key derivation + RSA-2048 for beneficiary keys)
- **Auth:** JWT tokens + bcrypt password hashing
- **Background jobs:** APScheduler (daily check-in cron)
- **Email:** SMTP / SendGrid

## Project Structure
```
lastkey/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, CORS, middleware
│   │   ├── config.py        # Settings, env vars
│   │   ├── database.py      # SQLAlchemy engine + session
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── routers/         # API endpoint groups
│   │   ├── services/        # Business logic + encryption
│   │   ├── middleware/       # Rate limiting, CSRF, auth
│   │   └── utils/           # Email, helpers
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/        # API calls (axios + JWT interceptor)
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## Database Models
- **User** — id, email, password_hash, name, check_in_interval_days, last_check_in_at, is_active
- **TrustedVerifier** — id, user_id (FK), name, email, verification_token, has_confirmed
- **Beneficiary** — id, user_id (FK), name, email, public_key
- **Secret** — id, user_id (FK), title, encrypted_content, encryption_iv, encryption_tag, secret_type (enum: password/note/document/file)
- **SecretAssignment** — id, secret_id (FK), beneficiary_id (FK), encrypted_key
- **AuditLog** — id, user_id, action, details, ip_address, created_at

## Key Design Decisions
- **Zero-knowledge encryption:** Server never stores plaintext secrets or unencrypted keys
- **Encryption flow:** Random AES-256 key per secret → content encrypted with AES-GCM → key encrypted with beneficiary's RSA public key → stored in SecretAssignment
- **Dead man's switch:** User sets check-in interval → missed check-in triggers reminder → grace period (7 days) → verifier contacted → verifier confirms → beneficiaries notified and receive secrets

## Security Requirements
- SQLAlchemy ORM only (no raw SQL)
- Rate limiting via slowapi on all endpoints (5 attempts/min on auth)
- CORS whitelisted to frontend origin only
- CSRF tokens on state-changing requests
- Security headers: HSTS, X-Content-Type-Options, X-Frame-Options, CSP
- Pydantic validation on all inputs
- Audit logging on all sensitive actions with IP + timestamp

## API Route Groups
- `/api/auth/*` — register, login, logout, me
- `/api/secrets/*` — CRUD for encrypted secrets
- `/api/beneficiaries/*` — manage beneficiaries + assign secrets
- `/api/verifier/*` — set/update trusted verifier
- `/api/verify/{token}/*` — public verifier confirmation/denial
- `/api/checkin` — one-click check-in from email
- `/api/settings/*` — check-in interval config

## Implementation Order
1. Project setup + FastAPI scaffold + DB connection
2. Database models + Alembic migrations
3. Authentication system (JWT + bcrypt)
4. Encryption service
5. Secrets management API
6. Beneficiary management API
7. Trusted verifier API
8. Dead man's switch (APScheduler background jobs)
9. Secret release flow
10. Security middleware
11. React frontend
12. Testing + polish

## Commands
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload        # Dev server on :8000
alembic upgrade head                  # Run migrations

# Frontend
cd frontend && npm install
npm start                             # Dev server on :3000
```

## Full Spec
See [crispy-bouncing-codd.md](crispy-bouncing-codd.md) for the complete project specification.
