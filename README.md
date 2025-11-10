# green-david-app – Calendar Buttons Hotfix (DELETE / EDIT / DETAIL)

This bundle contains **surgical patches** that fix the calendar buttons without touching layout/CSS.

## What’s fixed

1) **Wrong path `/gd/api/*` → 404/405**  
   Adds alias routes so `/gd/api/tasks` works the same as `/api/tasks` (GET, POST, PATCH/PUT, DELETE).

2) **`POST /api/tasks` 500: `NOT NULL constraint failed: tasks.created_at`**  
   The insert now sets `created_at` to `CURRENT_TIMESTAMP` so schema changes are not required.

3) **PATCH/PUT update for Edit button**  
   Accepts partial body for fields (`title`, `description`, `status`, `due_date`, `job_id`, `employee_id`).

4) **GET detail by `?id=`**  
   Returns a single task when `id` is provided, keeping current list behaviour otherwise.

## Files in this hotfix

- `patches/api_tasks_patch.py` – drop‑in replacement for your `api_tasks` view function in `main.py`.
- `patches/gd_api_alias_patch.py` – add once near your Flask routes to expose `/gd/api/tasks` as an alias.
- `sql/migration.sql` – optional safety migration if you prefer a DB default for `created_at`.
- `test/http_examples.http` – ready-to-run HTTP examples (Insomnia/VS Code REST Client format).

## Apply

1. **Open `main.py`** and replace your existing `api_tasks` function with the one from
   `patches/api_tasks_patch.py` (it has the same endpoint: `/api/tasks`).

2. **Add the alias route** from `patches/gd_api_alias_patch.py` (anywhere after `api_tasks`), so old
   frontend calls to `/gd/api/tasks` keep working.

3. (Optional) If you want DB-level defaults as well, run `sql/migration.sql` once on your SQLite DB.

4. **Redeploy**. No template/CSS changes required; existing buttons calling
   `DELETE /gd/api/tasks?id=…`, `PATCH /gd/api/tasks`, etc., will work immediately.

---

**Tip:** If your frontend calls `PUT` instead of `PATCH` for edits, the new handler supports both.
