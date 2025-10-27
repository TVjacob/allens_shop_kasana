# app/routes/users.py
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import jwt
from app import db
from app.models import User, Permission
from app.utils.auth import token_required, permission_required, role_required

users_bp = Blueprint("users", __name__, url_prefix="/users")

# ---------------- Authentication ---------------- #

@users_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    payload = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=4)
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "permissions": [p.name for p in user.permissions]
        }
    })
# @users_bp.route("/login", methods=["POST"])
# def login():
#     data = request.json
#     username = data.get("username")
#     password = data.get("password")

#     if not username or not password:
#         return jsonify({"error": "Username and password required"}), 400

#     user = User.query.filter_by(username=username).first()
#     if not user or not check_password_hash(user.password_hash, password):
#         return jsonify({"error": "Invalid credentials"}), 401

#     payload = {
#         "user_id": user.id,
#         "username": user.username,
#         "role": user.role,
#         "exp": datetime.utcnow() + timedelta(hours=4)  # token expires in 4 hours
#     }
#     token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

#     return jsonify({
#         "message": "Login successful",
#         "token": token,
#         "user": {
#             "id": user.id,
#             "username": user.username,
#             "role": user.role
#         }
#     })

# ---------------- User Management ---------------- #

@users_bp.route("/", methods=["POST"])
@token_required
@permission_required("create_user")
def create_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "Staff")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    user = User(
        username=username,
        role=role,
        status=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created", "user_id": user.id}), 201


@users_bp.route("/", methods=["GET"])
@token_required
@permission_required("view_users")
def get_users():
    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "status": u.status,
            "permissions": [p.name for p in u.permissions],
            "created_at": u.created_at,
            "updated_at": u.updated_at
        } for u in users
    ])


@users_bp.route("/<int:user_id>", methods=["PUT"])
@token_required
@permission_required("edit_user")
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json

    user.username = data.get("username", user.username)
    user.role = data.get("role", user.role)
    if "password" in data and data["password"]:
        user.set_password(data["password"])
    user.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"message": "User updated"})


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@token_required
@permission_required("delete_user")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"})


# ---------------- Permissions ---------------- #

@users_bp.route("/permissions", methods=["GET"])
@token_required
@permission_required("view_permissions")
def get_permissions():
    permissions = Permission.query.all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "status": p.status
        } for p in permissions
    ])


@users_bp.route("/<int:user_id>/permissions/<int:perm_id>", methods=["POST"])
@token_required
@permission_required("assign_permissions")
def assign_permission(user_id, perm_id):
    user = User.query.get_or_404(user_id)
    perm = Permission.query.get_or_404(perm_id)
    user.add_permission(perm)
    db.session.commit()
    return jsonify({"message": f"Permission '{perm.name}' assigned to {user.username}"})


@users_bp.route("/<int:user_id>/permissions/<int:perm_id>", methods=["DELETE"])
@token_required
@permission_required("assign_permissions")
def remove_permission(user_id, perm_id):
    user = User.query.get_or_404(user_id)
    perm = Permission.query.get_or_404(perm_id)
    user.remove_permission(perm)
    db.session.commit()
    return jsonify({"message": f"Permission '{perm.name}' removed from {user.username}"})


# ---------------- WhoAmI (Verify Token) ---------------- #

@users_bp.route("/me", methods=["GET"])
@token_required
def get_current_user():
    user = request.user
    return jsonify({
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "permissions": [p.name for p in user.permissions]
    })
