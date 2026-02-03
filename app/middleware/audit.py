from flask import request, g
from datetime import datetime
import uuid as uuid_lib
import json

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()


def setup_audit_middleware(app):
    """Nastaví audit middleware pro Flask app."""
    
    @app.before_request
    def before_request():
        g.request_id = str(uuid_lib.uuid4())
        g.request_start = datetime.utcnow()
    
    @app.after_request
    def after_request(response):
        # Loguj pouze API requesty
        if request.path.startswith('/api/tasks'):
            try:
                db = get_db()
                duration = (datetime.utcnow() - g.request_start).total_seconds() * 1000
                
                request_body = None
                if request.method in ['POST', 'PUT', 'PATCH']:
                    try:
                        request_body = request.get_json(silent=True)
                        if request_body:
                            request_body = json.dumps(request_body)
                    except:
                        pass
                
                db.execute("""
                    INSERT INTO audit_logs (
                        request_id, endpoint, method, user_id, request_body,
                        response_status, duration_ms, ip_address, user_agent, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    g.request_id,
                    request.path,
                    request.method,
                    getattr(g, 'current_user_id', None),
                    request_body,
                    response.status_code,
                    duration,
                    request.remote_addr,
                    request.user_agent.string[:500] if request.user_agent else None,
                    datetime.utcnow().isoformat()
                ))
                db.commit()
            except Exception as e:
                # Nechceme aby audit rozbil request
                print(f"[AUDIT ERROR] {e}")
        
        return response
