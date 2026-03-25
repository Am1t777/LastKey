# LastKey — Digital Inheritance Vault

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

## Authentication (Step 3)

The auth system uses **JWT tokens** (HS256) and **bcrypt** password hashing.

### How it works

1. **Register** — `POST /api/auth/register` with `{email, password, name}`. Password must be at least 8 characters. Returns a JWT token immediately (user is logged in after registration).
2. **Login** — `POST /api/auth/login` with `{email, password}`. Returns a JWT token. Uses a generic error message ("Invalid email or password") to prevent user enumeration.
3. **Access protected routes** — Include the token in the `Authorization: Bearer <token>` header.
4. **Get current user** — `GET /api/auth/me` returns the authenticated user's profile.
5. **Logout** — `POST /api/auth/logout`. Since JWTs are stateless, this logs the action and returns a success message.

### Files

| File | Purpose |
|---|---|
| `backend/app/schemas/auth.py` | Pydantic request/response models (UserRegister, UserLogin, TokenResponse, etc.) |
| `backend/app/services/auth_service.py` | Password hashing, JWT creation/validation, `get_current_user` dependency, audit logger |
| `backend/app/routers/auth.py` | Four auth endpoints under `/api/auth` |

### Key design decisions

- **`get_current_user` dependency** — reusable FastAPI dependency that all protected routes will use via `Depends(get_current_user)`
- **`log_audit` helper** — reusable function for audit logging across all routers
- **Stateless logout** — no token blocklist needed for a portfolio project; JWT simply expires after 30 minutes
- **Audit trail** — register, login, and logout actions are logged with user ID and IP address

---

## Encryption Service (Step 4)

All encryption logic lives in `backend/app/services/encryption_service.py`. It is a pure module — no DB access, no FastAPI dependencies, just crypto functions used by Steps 5–9.

### Functions

| Function | Description |
|---|---|
| `generate_aes_key()` | Returns 32 random bytes (AES-256 key) |
| `encrypt_content(plaintext, key)` | AES-256-GCM encrypt → `(ciphertext_b64, iv_b64, tag_b64)` |
| `decrypt_content(ct_b64, key, iv_b64, tag_b64)` | AES-256-GCM decrypt → plaintext string |
| `generate_rsa_keypair()` | RSA-2048 → `(public_pem, private_pem)` |
| `encrypt_key_for_beneficiary(aes_key, public_pem)` | RSA-OAEP encrypt AES key → base64 string |
| `decrypt_key_as_beneficiary(enc_key_b64, private_pem)` | RSA-OAEP decrypt → raw AES key bytes |
| `derive_key(password, salt)` | Argon2id (time=3, mem=64MB, p=4) → 32-byte key |

### How the zero-knowledge flow works

```
User creates a secret:
  plaintext → AES-256-GCM(key) → encrypted_content + iv + tag  (stored in secrets table)
  aes_key   → RSA-OAEP(beneficiary.public_key) → encrypted_key (stored in secret_assignments)

Beneficiary retrieves the secret:
  encrypted_key → RSA-OAEP decrypt(beneficiary.private_key) → aes_key
  encrypted_content → AES-256-GCM decrypt(aes_key, iv, tag) → plaintext
```

The server never holds plaintext secrets or unencrypted AES keys. Only beneficiaries have their RSA private keys.

An additional `owner_encrypted_key` is stored per secret (AES key encrypted with the owner's Argon2id-derived password key), allowing post-creation beneficiary assignment without breaking zero-knowledge — the server only touches the key in RAM for milliseconds.

---

## Secrets API (Step 5)

### Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/secrets` | Create a new secret (accepts `beneficiary_ids` for at-creation assignment) |
| GET | `/api/secrets` | List all secrets (metadata only, paginated) |
| GET | `/api/secrets/{id}` | Get one secret (encrypted blob) |
| PUT | `/api/secrets/{id}` | Update title / content / type |
| DELETE | `/api/secrets/{id}` | Delete secret + all its assignments |
| POST | `/api/secrets/{id}/assign` | Assign to a new beneficiary post-creation |

### Create request shape
```json
{
  "title": "Gmail",
  "content": "hunter2",
  "secret_type": "password",
  "password": "your_account_password",
  "beneficiary_ids": [1, 2]
}
```

`password` is used to derive an Argon2id key that encrypts the secret's AES key for the owner. Never stored in plaintext.

GET responses return encrypted blobs only — no server-side decryption.

---

## Beneficiaries API (Step 6)

### Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/beneficiaries` | Add a beneficiary |
| GET | `/api/beneficiaries` | List all beneficiaries |
| GET | `/api/beneficiaries/{id}` | Get one beneficiary |
| PATCH | `/api/beneficiaries/{id}` | Update name or email |
| DELETE | `/api/beneficiaries/{id}` | Delete beneficiary + assignments |
| POST | `/api/beneficiaries/{id}/generate-key` | Generate RSA-2048 keypair (returns private key once) |
| GET | `/api/beneficiaries/{id}/secrets` | List secrets assigned to this beneficiary |

### RSA key generation flow
1. Owner calls `POST /api/beneficiaries/{id}/generate-key`
2. Server generates RSA-2048 keypair — public key stored in DB, private key returned in response body
3. Owner delivers private key to beneficiary manually (copy-paste, printed, etc.)
4. Key rotation is not supported — delete and recreate the beneficiary to reset

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

## Trusted Verifier API (Step 7)

Each user may designate one trusted verifier (friend, doctor, lawyer) who can confirm death or incapacitation. The server generates two cryptographically random tokens per verifier — one for confirmation, one for denial — stored only in the DB and sent only via email links. Tokens are never exposed in any API response.

### Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/verifier` | Bearer | Set or silently replace the trusted verifier (upserts, regenerates tokens) |
| GET | `/api/verifier` | Bearer | Get current verifier |
| DELETE | `/api/verifier` | Bearer | Remove verifier |
| POST | `/api/verify/{token}/confirm` | None | Verifier confirms — must type user's full name to confirm |
| POST | `/api/verify/{token}/deny` | None | Verifier denies — resets the dead man's switch timer |

### Confirm flow
The verifier must submit `{"confirmation_text": "<user's full name>"}`. The name is compared case-insensitively. This prevents accidental one-click confirmation. If `switch_status != verifier_alerted`, both endpoints return `400` — preventing stale email links from taking effect.

---

## Dead Man's Switch (Step 8)

### State machine

```
[active]
   │ scheduler: deadline passed
   ▼
[reminder_sent] ◄──────────────────────────────────────────┐
   │ scheduler: +7 days grace period ends                  │
   ▼                                                       │
[verifier_alerted]                                         │
   │              │                                        │
   │ /confirm     │ /deny                                  │
   ▼              ▼                                        │
[released]      [active] (last_check_in_at = now) ─────────┘
```

Any check-in at any stage resets to `[active]`.

### Scheduler

APScheduler (`AsyncIOScheduler`) runs a daily cron job at 02:00 UTC. It processes every active user:
- **Overdue but in grace period** → sends one reminder email with a magic check-in link → `switch_status = reminder_sent`
- **Grace period expired, no verifier** → sends urgent warning email to the user
- **Grace period expired, verifier exists** → refreshes tokens, emails verifier with Confirm / Deny buttons → `switch_status = verifier_alerted`

The scheduler starts automatically via FastAPI's `lifespan` context manager and shuts down cleanly on server stop.

### Check-in endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/checkin` | None | Token-based (magic link from email) — body: `{"token": "..."}` |
| POST | `/api/checkin/auth` | Bearer | JWT-authenticated (dashboard button) |

Both reset `last_check_in_at`, clear all state fields, and return `{"message": "...", "next_checkin_due": "..."}`.

### New User fields

| Field | Type | Description |
|---|---|---|
| `switch_status` | enum | `active / reminder_sent / verifier_alerted / released` |
| `reminder_sent_at` | datetime | When the reminder email was sent |
| `verifier_contacted_at` | datetime | When the verifier was emailed |
| `checkin_token` | string | One-time magic-link token for email check-in |
| `checkin_token_expires_at` | datetime | Token expiry (30 days from issuance) |

---

## Secret Release Flow (Step 9)

When a trusted verifier confirms death, the system automatically releases all secrets to their designated beneficiaries.

### Flow

1. Verifier calls `POST /api/verify/{token}/confirm` with the deceased's name
2. `switch_status` → `released`, `released_at` timestamp set
3. For each beneficiary who has assigned secrets:
   - A unique 90-day release token is generated and stored
   - A notification email is sent with an "Access My Secrets" button
   - Audit entries logged per beneficiary
4. Beneficiary visits `{FRONTEND_URL}/release/{token}` → frontend calls `GET /api/release/{token}`
5. Server returns all encrypted blobs — beneficiary decrypts client-side with their RSA private key

### Retrieval endpoint

`GET /api/release/{token}` — no auth required, token is the credential:

```json
{
  "deceased_name": "John Smith",
  "beneficiary_name": "Alice Smith",
  "released_at": "2026-03-25T10:00:00",
  "secrets": [
    {
      "title": "Gmail",
      "secret_type": "password",
      "encrypted_content": "<base64>",
      "encryption_iv": "<base64>",
      "encryption_tag": "<base64>",
      "encrypted_key": "<base64 AES key encrypted with beneficiary's RSA public key>"
    }
  ]
}
```

The server never decrypts anything — zero-knowledge is maintained.

### New fields

| Table | Field | Description |
|---|---|---|
| `beneficiaries` | `release_token` | Unique 90-day token sent in release email |
| `beneficiaries` | `release_token_expires_at` | Token expiry datetime |
| `users` | `released_at` | When the release was triggered |

### Audit log actions

| Action | Trigger |
|---|---|
| `release.triggered` | Summary entry (beneficiary count) |
| `release.notified` | Per-beneficiary email sent successfully |
| `release.email_failed` | Per-beneficiary SMTP failure (silent, logged only) |
| `release.accessed` | `GET /api/release/{token}` called |

---

## Security Middleware (Step 10)

### Rate limiting (slowapi)

| Endpoint | Limit |
|---|---|
| `POST /api/auth/register` | 5/minute per IP |
| `POST /api/auth/login` | 5/minute per IP |
| `POST /api/checkin` | 20/minute per IP |
| `POST /api/verify/{token}/confirm` | 10/minute per IP |
| `POST /api/verify/{token}/deny` | 10/minute per IP |

Returns `429 Too Many Requests` when exceeded. Uses in-memory storage (single-worker dev/demo).

### CSRF protection

`X-Requested-With` header required on all `POST/PUT/PATCH/DELETE` requests to `/api/*`. Returns `403` if missing.

Exempt paths (called from email links, no JS available):
- `POST /api/checkin` — magic-link check-in
- `POST /api/verify/{token}/confirm` and `/deny` — verifier confirmation

### Security response headers

Applied to every response by `SecurityHeadersMiddleware`:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` (relaxed for `/docs`) |

### Other hardening

- CORS `allow_headers` tightened to `Authorization, Content-Type, X-Requested-With`
- `/docs` and `/redoc` disabled when `APP_ENV=production`

---

## Implementation Progress

- [x] Step 1 — Project setup: FastAPI scaffold, SQLite, config, health endpoint
- [x] Step 2 — Database models: all 6 tables with relationships
- [x] Step 3 — Authentication: register, login, JWT, bcrypt
- [x] Step 4 — Encryption service: AES-256-GCM + RSA-2048
- [x] Step 5 — Secrets API: CRUD
- [x] Step 6 — Beneficiaries API
- [x] Step 7 — Trusted verifier API
- [x] Step 8 — Dead man's switch (APScheduler)
- [x] Step 9 — Secret release flow
- [x] Step 10 — Security middleware
- [ ] Step 11 — React frontend
- [ ] Step 12 — Testing + polish
