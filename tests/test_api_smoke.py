import os
import unittest
import sqlite3
from datetime import datetime

# IMPORTANT:
# - run_tests.py sets DB_PATH before importing main.py
# - main.py will create schema + default admin user automatically

class APISmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Import app only after DB_PATH is set (run_tests.py does it).
        import main  # noqa
        cls.main = main
        cls.app = main.app
        cls.app.config["TESTING"] = True

    def setUp(self):
        self.client = self.app.test_client()
        # Ensure we are authenticated for endpoints that require login.
        self._login_as_admin()

    def _login_as_admin(self):
        email = os.environ.get("ADMIN_EMAIL", "admin@greendavid.local")
        password = os.environ.get("ADMIN_PASSWORD", "admin123")
        resp = self.client.post("/api/login", json={"email": email, "password": password})
        self.assertIn(resp.status_code, (200, 204), resp.get_data(as_text=True))

    def _seed_minimal_data(self):
        """Insert deterministic records so /api/search can be contract-tested."""
        token = "zzseedtoken"
        # Use the same DB that main.py uses (DB_PATH env var).
        db_path = os.environ["DB_PATH"]
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Employees
        # employees table exists in this app; keep columns minimal and compatible.
        # We add a single employee that contains the token.
        cur.execute("INSERT INTO employees (name, email) VALUES (?, ?)", (f"Seed {token}", f"{token}@example.com"))
        emp_id = cur.lastrowid

        # Jobs
        # Prefer columns that exist across versions: title/name, client, city, note, status, code, date
        # We'll try title first, fallback to name if needed.
        cols = [r[1] for r in cur.execute("PRAGMA table_info(jobs)").fetchall()]
        if "title" in cols:
            cur.execute(
                "INSERT INTO jobs (title, client, city, note, status, code, date) VALUES (?,?,?,?,?,?,?)",
                (f"Job {token}", f"Client {token}", "Prague", f"Note {token}", "active", token, datetime.utcnow().date().isoformat()),
            )
        else:
            cur.execute(
                "INSERT INTO jobs (name, client, city, note, status, code, date) VALUES (?,?,?,?,?,?,?)",
                (f"Job {token}", f"Client {token}", "Prague", f"Note {token}", "active", token, datetime.utcnow().date().isoformat()),
            )
        job_id = cur.lastrowid

        # Tasks
        tcols = [r[1] for r in cur.execute("PRAGMA table_info(tasks)").fetchall()]
        if "title" in tcols:
            cur.execute(
                "INSERT INTO tasks (job_id, title, description, status) VALUES (?,?,?,?)",
                (job_id, f"Task {token}", f"Desc {token}", "open"),
            )
        else:
            cur.execute(
                "INSERT INTO tasks (job_id, name, description, status) VALUES (?,?,?,?)",
                (job_id, f"Task {token}", f"Desc {token}", "open"),
            )
        task_id = cur.lastrowid

        # Issues
        icols = [r[1] for r in cur.execute("PRAGMA table_info(issues)").fetchall()]
        title_col = "title" if "title" in icols else ("name" if "name" in icols else None)
        if title_col:
            cur.execute(
                f"INSERT INTO issues (job_id, {title_col}, description, status) VALUES (?,?,?,?)",
                (job_id, f"Issue {token}", f"Issue desc {token}", "open"),
            )
        else:
            # If issues schema differs drastically, skip seeding issues (contract test will allow empty issues if table lacks cols).
            pass

        con.commit()
        con.close()
        return token

    def test_api_me(self):
        resp = self.client.get("/api/me")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("authenticated"))

    def test_api_search_min_length(self):
        resp = self.client.get("/api/search?q=a")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("ok"))
        self.assertIn("results", data)

    def test_api_search_shape_and_no_500(self):
        resp = self.client.get("/api/search?q=david")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()
        self.assertTrue(data.get("ok"))
        self.assertIn("results", data)
        results = data["results"]
        # Must always exist as lists
        for key in ("jobs", "tasks", "issues", "employees"):
            self.assertIn(key, results)
            self.assertIsInstance(results[key], list)
        self.assertIn("total", data)
        self.assertIsInstance(data["total"], int)
        self.assertGreaterEqual(data["total"], 0)

    def test_api_search_contract_with_seed(self):
        token = self._seed_minimal_data()
        resp = self.client.get(f"/api/search?q={token}")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()
        self.assertTrue(data.get("ok"))
        results = data["results"]
        # Expect at least one match in jobs, tasks, employees. Issues may be empty if schema differs.
        self.assertGreaterEqual(len(results["jobs"]), 1)
        self.assertGreaterEqual(len(results["tasks"]), 1)
        self.assertGreaterEqual(len(results["employees"]), 1)

        # Minimal contract keys (avoid overly strict coupling to UI)
        def has_any(obj, keys):
            return any(k in obj and obj.get(k) not in (None, "") for k in keys)

        self.assertTrue(has_any(results["jobs"][0], ["id"]))
        self.assertTrue(has_any(results["jobs"][0], ["name", "title"]))
        self.assertTrue(has_any(results["tasks"][0], ["id"]))
        self.assertTrue(has_any(results["tasks"][0], ["title", "name"]))
        self.assertTrue(has_any(results["employees"][0], ["id"]))
        self.assertTrue(has_any(results["employees"][0], ["name", "email"]))

    def test_smoke_key_list_endpoints(self):
        for path in ("/api/jobs", "/api/tasks", "/api/issues", "/api/employees"):
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, f"{path} -> {resp.status_code}: {resp.get_data(as_text=True)[:200]}")

    def test_contract_list_endpoints_min_keys(self):
        # Jobs
        jobs = self.client.get("/api/jobs").get_json()
        self.assertTrue(jobs.get("ok"))
        jitems = jobs.get("jobs") or jobs.get("items") or []
        if jitems:
            j0 = jitems[0]
            self.assertIn("id", j0)
            self.assertTrue(("name" in j0) or ("title" in j0))

        # Tasks
        tasks = self.client.get("/api/tasks").get_json()
        self.assertTrue(tasks.get("ok"))
        titems = tasks.get("tasks") or tasks.get("items") or []
        if titems:
            t0 = titems[0]
            self.assertIn("id", t0)
            self.assertTrue(("title" in t0) or ("name" in t0))
            self.assertIn("status", t0)

        # Issues
        issues = self.client.get("/api/issues").get_json()
        self.assertTrue(issues.get("ok"))
        iitems = issues.get("issues") or issues.get("items") or []
        if iitems:
            i0 = iitems[0]
            self.assertIn("id", i0)
            self.assertTrue(("title" in i0) or ("name" in i0))
            self.assertIn("status", i0)

        # Employees
        emps = self.client.get("/api/employees").get_json()
        self.assertTrue(emps.get("ok"))
        eitems = emps.get("employees") or emps.get("items") or []
        if eitems:
            e0 = eitems[0]
            self.assertIn("id", e0)
            self.assertTrue(("name" in e0) or ("email" in e0))
