# ECO-Dating — Vercel deployment (Neon PostgreSQL)

## 1. Create free PostgreSQL (Neon)

1. Go to [neon.tech](https://neon.tech) and create a project.
2. Copy the **Pooled connection** string (must start with `postgresql://`).
3. It should include `?sslmode=require` at the end.

You can also use Supabase or Railway PostgreSQL — any provider that gives a `DATABASE_URL`.

---

## 2. Vercel environment variables

In Vercel → your project → **Settings → Environment Variables**, add:

| Name | Value | Environments |
|------|-------|----------------|
| `SECRET_KEY` | Run: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` | Production, Preview, Development |
| `DEBUG` | `False` | Production, Preview |
| `DATABASE_URL` | Your Neon pooled URL | Production, Preview, Development |
| `ALLOWED_HOSTS` | `.vercel.app` | Production, Preview |
| `CSRF_TRUSTED_ORIGINS` | `https://YOUR-PROJECT.vercel.app` (update after first deploy) | Production |

`VERCEL_URL` is set automatically by Vercel and added to `ALLOWED_HOSTS` / CSRF in `settings.py`.

---

## 3. Deploy on Vercel

1. Push this repo to GitHub.
2. [vercel.com](https://vercel.com) → **Add New** → **Project** → import repo.
3. Framework Preset: **Other**
4. Root Directory: `.` (repository root)
5. Add env vars from step 2 **before** deploying.
6. Deploy.

`build.sh` runs automatically:

- `collectstatic` (Whitenoise)
- `migrate` (creates `auth_user` and all tables)

7. After deploy, open:

- `https://YOUR-PROJECT.vercel.app/` — homepage
- `https://YOUR-PROJECT.vercel.app/health/` — should return `{"status": "ok"}`

8. Update `CSRF_TRUSTED_ORIGINS` with your real URL and redeploy if login/signup shows CSRF errors.

---

## 4. Create admin user (optional)

Use Vercel CLI locally with production env, or run once from your machine:

```bash
set DATABASE_URL=your-neon-url
set SECRET_KEY=your-secret
python manage.py createsuperuser
```

---

## 5. Local development

```powershell
cd eco_backup
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/

Leave `DATABASE_URL` empty locally to use SQLite.

---

## 6. Troubleshooting

| Error | Fix |
|-------|-----|
| 500 / Serverless Function crashed | Vercel → Deployments → **Functions** → view logs |
| `DATABASE_URL is required on Vercel` | Add `DATABASE_URL` in Vercel env vars, redeploy |
| `Set a strong SECRET_KEY` | Add `SECRET_KEY` in Vercel env vars |
| `no such table: auth_user` | Ensure `DATABASE_URL` is set; redeploy so `build.sh` runs `migrate` |
| `unable to open database file` | `DATABASE_URL` missing — Vercel cannot use SQLite |
| CSRF failed on login | Add exact `https://your-app.vercel.app` to `CSRF_TRUSTED_ORIGINS` |
| Static/CSS broken | Check build logs for `collectstatic`; Whitenoise serves `/static/` |
| Profile photos disappear | Vercel serverless has no persistent disk — expected on free tier |

---

## Notes

- **WSGI only** — no Daphne/Channels (chat uses HTTP polling).
- **Gunicorn** is in `requirements.txt` for Railway; Vercel uses `api/index.py` directly.
- Profile image uploads are temporary on Vercel unless you add S3/Cloudinary later.
