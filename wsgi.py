"""
WSGI Entry Point for Gunicorn
Green David App v2.0
"""

from main import app

# Gunicorn uses: wsgi:app

if __name__ == "__main__":
    app.run()
