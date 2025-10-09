import os, importlib
from flask import Flask, send_from_directory

# Try to import an existing app object or factory from common module names
def load_existing_app():
    candidates = [
        ('main_app','app'), ('main_app','create_app'),
        ('server','app'), ('server','create_app'),
        ('application','app'), ('application','create_app'),
        ('app','app'), ('app','create_app'),
    ]
    for mod_name, attr in candidates:
        try:
            mod = importlib.import_module(mod_name)
            obj = getattr(mod, attr, None)
            if callable(obj):
                a = obj()
                if a is not None:
                    return a
            elif obj is not None:
                return obj
        except Exception:
            continue
    return None

app = load_existing_app()
if app is None:
    # Fallback minimal app so Gunicorn has something to run
    app = Flask(__name__, static_folder='.', static_url_path='')

    @app.route('/')
    def index():
        # Serve index.html if present; otherwise a simple health text
        try:
            return app.send_static_file('index.html')
        except Exception:
            return 'OK', 200

    @app.route('/health')
    def health():
        return {'ok': True}, 200

    @app.route('/static/<path:p>')
    def static_proxy(p):
        return send_from_directory('static', p)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
