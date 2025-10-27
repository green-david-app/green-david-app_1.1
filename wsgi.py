
# WSGI using the proper app factory + built-in redirect for /calendar.html
from app import create_app
from flask import redirect

app = create_app()

# Force server-side redirect so Safari/Chrome don't loop on meta refresh
@app.route("/calendar.html")
def _redirect_calendar_html():
    return redirect("/calendar", code=302)

# gunicorn entrypoint: wsgi:app
