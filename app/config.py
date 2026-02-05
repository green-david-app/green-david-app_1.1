import os

# Database path configuration
# Priority: 1. DB_PATH env var, 2. Persistent disk detection, 3. Default
if os.environ.get("DB_PATH"):
    # User explicitly set DB_PATH - use it
    DATABASE = os.environ.get("DB_PATH")
elif os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    # Render platform detected - try persistent disk paths
    if os.path.exists("/persistent"):
        DATABASE = "/persistent/app.db"
    elif os.path.exists("/data"):
        DATABASE = "/data/app.db"
    else:
        # Fallback to /tmp which is persistent on Render
        DATABASE = "/tmp/app.db"
else:
    # Local development
    DATABASE = "app.db"

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())
UPLOAD_FOLDER = os.environ.get("UPLOAD_DIR", "uploads")

# Flask app configuration
SEND_FILE_MAX_AGE_DEFAULT = 0

# Role definitions
# Pozn.: role 'team_lead' byla v předchozích verzích; pro kompatibilitu ji mapujeme na 'lander'.
ROLES = ("owner", "admin", "manager", "lander", "worker")
WRITE_ROLES = ("owner", "admin", "manager", "lander")

# Role pro zaměstnance v UI (enterprise: jednotné a jednoduché)
EMPLOYEE_ROLES = ("owner", "manager", "lander", "worker")

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
