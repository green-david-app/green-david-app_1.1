import os, io, csv
from flask import Flask, jsonify, request, send_file, render_template, redirect, url_for
# ... (rest of imports and app setup are assumed above in your existing file)

app = Flask(__name__)  # keep your existing config

# --- existing endpoints are here ---

# ----------------- Template routes (unified design) -----------------
@app.route("/timesheets")
def page_timesheets():
    # Render via Jinja so that {% extends "layout.html" %} works, bringing in app fonts/styles.
    return render_template("timesheets.html", title="Výkazy")

# Backward compatibility for any old links:
@app.route("/timesheets.html")
def page_timesheets_legacy():
    return redirect(url_for("page_timesheets"), code=301)

# ... keep the rest of your main.py content unchanged ...
