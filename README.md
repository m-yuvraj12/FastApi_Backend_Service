# Push Notification Backend (FastAPI + JWT + PostgreSQL + FCM)

Register/login users, register an Android device's FCM token, send push notifications through
Firebase Cloud Messaging, persist every successfully sent notification, and list what you've sent.

## Architecture

```
Swagger UI ──JWT──▶ FastAPI ──▶ PostgreSQL (users, devices, notifications)
                       │
                       └──▶ Firebase Admin SDK ──▶ FCM ──▶ Android device
```

```
app/
  main.py            app factory, router wiring, error handler, /health
  config.py          env-driven settings (pydantic-settings)
  database.py        engine, session, Base (with constraint naming convention)
  models.py          User, Device, Notification
  schemas.py         request/response models + validation
  security.py        bcrypt hashing, JWT create/decode
  deps.py            get_current_user (Bearer auth dependency)
  routers/           auth.py · devices.py · notifications.py
  services/fcm.py    Firebase Admin wrapper
migrations/          Alembic (versions/0001_initial_schema.py)
tests/               pytest suite (FCM mocked)
docker-compose.yml   api + postgres        Dockerfile / docker-entrypoint.sh
```

### Data model
| Table | Purpose | Key columns |
|---|---|---|
| `users` | accounts | `email` (unique), `hashed_password` (bcrypt), `is_active` |
| `devices` | Android FCM tokens | `user_id` → users, `fcm_token` (unique), `name` |
| `notifications` | sent messages | `user_id` → users, `title`, `body`, `data` (JSON), `target`, `delivered_count`, `fcm_message_ids`, `created_at` |

A notification row is written **only after FCM accepts the message**. Failed sends return an error and are not stored.

### Authentication flow
1. `POST /auth/register` – email + password (8–64 chars). Password stored as a bcrypt hash.
2. `POST /auth/login` – OAuth2 password form (`username` = your email). Returns a signed JWT (HS256, `sub` = user id, `exp`).
3. Send `Authorization: Bearer <token>` on every other call. In Swagger click **Authorize** and enter email/password.

### Migrations
Alembic manages the schema. The container entrypoint runs `alembic upgrade head` on every start, so a fresh
DB is created and later schema changes apply automatically. To change the schema:
```bash
# edit app/models.py, then
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Setup

### 1. Firebase (one-time)
1. Create a Firebase project → add an **Android app** (package name of your app) → download `google-services.json` for the app.
2. **Project settings → Service accounts → Generate new private key**. Save it as
   **`secrets/firebase-service-account.json`** (git-ignored – never commit it).
3. Build the Android receiver – see [`docs/android_quickstart.md`](docs/android_quickstart.md).
   It displays the device's FCM token.

### 2. Run with Docker
```bash
cp .env.example .env
# edit .env: set POSTGRES_PASSWORD and SECRET_KEY
docker compose up --build
```
Swagger UI: **http://localhost:8000/docs** · Health: http://localhost:8000/health

### 3. Try it (Swagger)
1. `POST /auth/register` → `{"email":"me@example.com","password":"password123"}`
2. Click **Authorize** → username `me@example.com`, password `password123`.
3. `PUT /devices` → `{"fcm_token":"<token shown in the Android app>","name":"My phone"}`
4. `POST /notifications/send` → `{"title":"Hello","body":"From Swagger"}` → **the notification appears on the phone** (sent to all your registered devices; add `"device_token"` to target one token explicitly).
5. `GET /notifications` → list of what you've sent (`limit`/`offset` pagination, newest first).

Inspect the DB:
```bash
docker compose exec db psql -U postgres -d notifications -c "select id,user_id,title,body,delivered_count,created_at from notifications;"
```

### curl equivalent
```bash
curl -X POST localhost:8000/auth/register -H 'content-type: application/json' -d '{"email":"me@example.com","password":"password123"}'
TOKEN=$(curl -s -X POST localhost:8000/auth/login -d 'username=me@example.com&password=password123' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -X PUT localhost:8000/devices -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' -d '{"fcm_token":"<FCM_TOKEN>"}'
curl -X POST localhost:8000/notifications/send -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' -d '{"title":"Hello","body":"From curl"}'
curl localhost:8000/notifications -H "Authorization: Bearer $TOKEN"
```

## API summary
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/auth/register` | – | 201 · 409 duplicate · 422 invalid |
| POST | `/auth/login` | – | 200 token · 401 bad credentials |
| GET | `/auth/me` | ✔ | current user |
| PUT / GET | `/devices` | ✔ | register / list FCM tokens |
| DELETE | `/devices/{id}` | ✔ | 204 · 404 |
| POST | `/notifications/send` | ✔ | 201 · 400 no device · 422 · 502 FCM failure · 503 FCM not configured |
| GET | `/notifications` | ✔ | only the caller's notifications, paginated |
| GET | `/notifications/{id}` | ✔ | 404 if not yours |

Stale tokens (FCM `UNREGISTERED`) are removed from `devices` automatically.

## Tests / local dev without Docker
```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
pytest                               # uses in-memory SQLite, FCM mocked
cp .env.example .env                 # set DATABASE_URL (uncomment) to a local Postgres
alembic upgrade head && uvicorn app.main:app --reload
```
`FCM_DRY_RUN=true` makes FCM validate requests without delivering (handy for CI).

## Troubleshooting
- **503 "Push service is not configured"** – `secrets/firebase-service-account.json` missing.
- **502 "Requested entity was not found"/Unregistered** – token is stale; re-copy it from the app.
- **502 SenderId mismatch** – the Android app's `google-services.json` and the service-account key must come from the *same* Firebase project.
- **No notification on device** – grant the notification permission (Android 13+), and use an emulator image *with Google Play*.

## Demo video checklist
1. Project structure (tree above) → 2. register/login/Authorize → 3. `models.py` + `migrations/` + `alembic upgrade head` in the container log
→ 4. `PUT /devices`, `POST /notifications/send` in Swagger → 5. phone receiving it → 6. `psql` select showing the row → 7. `GET /notifications`.
