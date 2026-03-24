# LastKey — Digital Inheritance Vault

A portfolio project for junior software engineering interviews.

LastKey lets users securely store encrypted secrets (passwords, documents, notes) that are automatically released to designated beneficiaries after the user's death or incapacitation — verified through a trusted person acting as a "dead man's switch".

---

## How it works (Big Picture)

1. **User registers** and stores their secrets (passwords, notes, documents) — all encrypted client-side before reaching the server.
2. **User designates beneficiaries** (family, lawyer, etc.) and assigns secrets to them.
3. **User sets a check-in interval** (e.g. every 30 days). They receive an email reminder to check in.
4. If the user **misses a check-in**, a grace period starts (7 days), then a **trusted verifier** (a friend, doctor, etc.) is contacted.
5. The verifier **confirms or denies** the user's death/incapacitation via a one-click email link.
6. If confirmed, beneficiaries are **notified and receive their assigned secrets**.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python + FastAPI |
| Frontend | React |
| Database | SQLite (dev) → PostgreSQL (prod) |
| ORM | SQLAlchemy + Alembic migrations |
| Encryption | AES-256-GCM + RSA-2048 (`cryptography` lib) |
| Auth | JWT tokens + bcrypt password hashing |
| Background jobs | APScheduler (daily check-in cron) |
| Email | SMTP / SendGrid |

---

## Project Structure

```
lastkey/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point, CORS, startup
│   │   ├── config.py         # Settings loaded from .env
│   │   ├── database.py       # SQLAlchemy engine + session + get_db()
│   │   ├── models/           # Database table definitions (SQLAlchemy)
│   │   ├── schemas/          # Request/response shapes (Pydantic)
│   │   ├── routers/          # API endpoint groups
│   │   ├── services/         # Business logic + encryption
│   │   ├── middleware/        # Rate limiting, CSRF, auth
│   │   └── utils/            # Email helpers
│   ├── requirements.txt
│   └── .env                  # Environment variables (not committed)
├── frontend/
│   └── ...                   # React app (coming soon)
├── CLAUDE.md                 # Project instructions for AI assistant
└── README.md                 # This file
```

---

## Database Models

### `User`
The main account. Stores login credentials and check-in settings.

| Field | Type | Description |
|---|---|---|
| id | int | Primary key |
| email | string | Unique login email |
| password_hash | string | bcrypt hashed password |
| name | string | Display name |
| check_in_interval_days | int | How often the user must check in (default: 30) |
| last_check_in_at | datetime | Last time the user checked in |
| is_active | bool | Account active flag |
| created_at | datetime | Account creation timestamp |

### `TrustedVerifier`
One trusted person per user who can confirm the user has passed away.

| Field | Type | Description |
|---|---|---|
| id | int | Primary key |
| user_id | int (FK) | The user this verifier belongs to |
| name | string | Verifier's name |
| email | string | Verifier's email |
| verification_token | string | Unique token sent in the confirmation email |
| has_confirmed | bool | Whether the verifier has confirmed death/incapacitation |

### `Beneficiary`
People who will receive the user's secrets.

| Field | Type | Description |
|---|---|---|
| id | int | Primary key |
| user_id | int (FK) | The user this beneficiary belongs to |
| name | string | Beneficiary's name |
| email | string | Beneficiary's email |
| public_key | text | RSA-2048 public key (PEM format) used to encrypt their secrets |

### `Secret`
An encrypted piece of data (password, note, document, or file).

| Field | Type | Description |
|---|---|---|
| id | int | Primary key |
| user_id | int (FK) | Owner of the secret |
| title | string | Human-readable name (e.g. "Gmail password") |
| encrypted_content | text | AES-256-GCM ciphertext, base64 encoded |
| encryption_iv | string | GCM nonce (initialization vector), base64 encoded |
| encryption_tag | string | GCM authentication tag, base64 encoded |
| secret_type | enum | One of: `password`, `note`, `document`, `file` |
| created_at / updated_at | datetime | Timestamps |

### `SecretAssignment`
Links a secret to a beneficiary. Stores the AES key encrypted for that specific beneficiary.

| Field | Type | Description |
|---|---|---|
| id | int | Primary key |
| secret_id | int (FK) | The secret being assigned |
| beneficiary_id | int (FK) | The recipient |
| encrypted_key | text | The secret's AES key, encrypted with the beneficiary's RSA public key |

> This is the heart of zero-knowledge encryption. The server never holds a plaintext key.

### `AuditLog`
Immutable record of all sensitive actions.

| Field | Type | Description |
|---|---|---|
| id | int | Primary key |
| user_id | int (nullable) | Who performed the action (null for pre-auth events) |
| action | string | Event name e.g. `user.login`, `secret.create` |
| details | text | JSON string with extra context |
| ip_address | string | Request IP |
| created_at | datetime | When it happened |

---

## Encryption Design (Zero-Knowledge)

The server **never sees plaintext secrets or unencrypted keys**. Here's how it works:

```
Secret content
    │
    ▼
[Random AES-256 key generated per secret]
    │
    ├──► AES-256-GCM encrypt(content) ──► stored in secrets.encrypted_content
    │
    └──► RSA encrypt(aes_key, beneficiary.public_key) ──► stored in secret_assignments.encrypted_key
```

When the secret is released to a beneficiary:
- They use their **RSA private key** (only they have it) to decrypt the AES key
- Then use the AES key to decrypt the content

---

## Security Features

- **No raw SQL** — SQLAlchemy ORM only, prevents SQL injection
- **Rate limiting** — slowapi, max 5 auth attempts/min
- **CORS** — only the frontend origin is whitelisted
- **CSRF protection** — tokens on all state-changing requests
- **Security headers** — HSTS, X-Frame-Options, CSP, X-Content-Type-Options
- **Audit logging** — every sensitive action logged with IP + timestamp
- **bcrypt** — passwords hashed with bcrypt (never stored plaintext)
- **JWT** — stateless auth tokens with expiry

---

## Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# API: http://localhost:8000
# Interactive docs: http://localhost:8000/docs

# Frontend (coming soon)
cd frontend
npm install
npm start
# App: http://localhost:3000
```

---

## API Endpoints (planned)

| Group | Prefix | Description |
|---|---|---|
| Auth | `/api/auth/*` | Register, login, logout, current user |
| Secrets | `/api/secrets/*` | CRUD for encrypted secrets |
| Beneficiaries | `/api/beneficiaries/*` | Manage beneficiaries + assign secrets |
| Verifier | `/api/verifier/*` | Set/update trusted verifier |
| Public verify | `/api/verify/{token}/*` | Verifier confirms/denies (no login needed) |
| Check-in | `/api/checkin` | One-click check-in from email link |
| Settings | `/api/settings/*` | Check-in interval and account settings |

---

## Implementation Progress

- [x] Step 1 — Project setup: FastAPI scaffold, SQLite, config, health endpoint
- [x] Step 2 — Database models: all 6 tables with relationships
- [ ] Step 3 — Authentication: register, login, JWT, bcrypt
- [ ] Step 4 — Encryption service: AES-256-GCM + RSA-2048
- [ ] Step 5 — Secrets API: CRUD
- [ ] Step 6 — Beneficiaries API
- [ ] Step 7 — Trusted verifier API
- [ ] Step 8 — Dead man's switch (APScheduler)
- [ ] Step 9 — Secret release flow
- [ ] Step 10 — Security middleware
- [ ] Step 11 — React frontend
- [ ] Step 12 — Testing + polish
