# Green David App (work-in-progress)

## Local run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```
Open: http://127.0.0.1:5000

## Deployment
This repository contains:
- `requirements.txt`
- `Procfile` (Gunicorn)
- `runtime.txt` (Python runtime hint)

For platforms that run Gunicorn, use:
- `main:app` (or `wsgi:app`)

Example command:
```bash
gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} main:app
```

## Notes
- The local SQLite database (`app.db`) is ignored by `.gitignore`.
- Uploaded files are stored under `./uploads/` and are ignored by `.gitignore`.
- List registered API routes: `GET /api/_routes`
