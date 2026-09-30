# Demo video script (~5-6 min)

**Before recording:** `docker compose up --build` running, Android app installed (token visible), Swagger open at /docs, a terminal ready for psql, phone screen mirrored/recorded (e.g. scrcpy).

1. **Structure & architecture (45s)** – show the tree in README. Say: routers → deps (JWT) → services/fcm → Postgres; Alembic runs at container start.
2. **Auth flow (60s)** – `POST /auth/register`; click **Authorize** (email as username); show `GET /auth/me` succeeds; show a call without a token returning 401. Mention bcrypt + HS256 JWT with expiry.
3. **DB & migrations (60s)** – open `models.py` (users/devices/notifications) and `migrations/versions/0001_initial_schema.py`; show container log line "Running upgrade -> 0001"; run `docker compose exec db psql -U postgres -d notifications -c '\dt'`.
4. **Register device (20s)** – paste token from the phone into `PUT /devices`.
5. **Send from Swagger (45s)** – `POST /notifications/send` `{"title":"Hello","body":"From Swagger"}` → 201 response.
6. **Received on Android (20s)** – show the notification arriving on the phone.
7. **Stored in DB (30s)** – `select id,user_id,title,body,delivered_count,created_at from notifications;`
8. **Fetch history (30s)** – `GET /notifications`; optionally show 422 for an empty title and that a second user sees an empty list.
