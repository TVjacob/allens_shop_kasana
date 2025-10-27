# app/utils/auth.py
from flask import request, jsonify, current_app
from functools import wraps
import jwt
from app.models import User, Permission
from app import db

def token_required(f):
    """Require a valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            # Expecting "Bearer <token>"
            token = token.split(" ")[1]
            data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            user = db.session.get(User, data["user_id"])
            if not user:
                return jsonify({"error": "User not found"}), 404
            request.user = user
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Ensure user has one of the specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, "user"):
                return jsonify({"error": "Authentication required"}), 401
            if request.user.role not in roles:
                return jsonify({"error": "Access denied"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def permission_required(permission_name):
    """Ensure user has the required permission."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, "user"):
                return jsonify({"error": "Authentication required"}), 401

            user_perms = [p.name for p in request.user.permissions]
            if permission_name not in user_perms:
                return jsonify({
                    "error": f"Permission '{permission_name}' required"
                }), 403

            return f(*args, **kwargs)
        return decorated
    return decorator
