#!/usr/bin/env python3
import sqlite3, sys, pathlib

db_path = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "data.db")
sql_path = pathlib.Path("migrations/2025-11-09_fix_tasks_created_at.sql")

print(f"Applying migration to {db_path} using {sql_path} ...")
con = sqlite3.connect(db_path)
with open(sql_path, "r", encoding="utf-8") as f:
    con.executescript(f.read())
con.close()
print("Done.")