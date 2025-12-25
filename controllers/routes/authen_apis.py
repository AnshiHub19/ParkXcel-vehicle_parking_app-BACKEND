from flask_restful import Resource
from flask import request, jsonify
from controllers.models import User, Roles
from controllers.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from functools import wraps
from datetime import timedelta

# ------------------------ Role-based decorators ------------------------
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        if not user or "admin" not in [r.name for r in user.roles]:
            return {"message": "Admin access required"}, 403
        return fn(*args, **kwargs)
    return wrapper

def user_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        if not user or "user" not in [r.name for r in user.roles]:
            return {"message": "User access required"}, 403
        return fn(*args, **kwargs)
    return wrapper

# ------------------------ Login API ------------------------
class LoginAPI(Resource):
    def post(self):
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return {"message": "Username/email and password required"}, 400

        username_or_email = data.get('username')
        password = data.get('password')

        # Find user by email or name
        user = User.query.filter((User.email == username_or_email) | (User.name == username_or_email)).first()
        if not user:
            return {"message": "User does not exist"}, 404

        if not check_password_hash(user.password, password):
            return {"message": "Invalid password"}, 401

        # Create JWT token (valid for 8 hours)
        access_token = create_access_token(
            identity=user.email,
            additional_claims={"roles": [r.name for r in user.roles]},
            expires_delta=timedelta(hours=8)
        )

        return {
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "name": user.name,
                "email": user.email,
                "roles": [r.name for r in user.roles],
                "user_role": [r.name for r in user.roles][0]  # first role
            }
        }, 200

# ------------------------ Register API ------------------------
class RegisterAPI(Resource):
    def post(self):
        data = request.get_json()
        if not data or 'username' not in data or 'email' not in data or 'password' not in data:
            return {"message": "Username, email, and password required"}, 400

        if User.query.filter_by(name=data.get('username')).first():
            return {"message": "Username already exists"}, 409
        if User.query.filter_by(email=data.get('email')).first():
            return {"message": "Email already registered"}, 409
        if len(data.get('password')) < 6:
            return {"message": "Password must be at least 6 characters"}, 400

        # Assign user role
        user_role = Roles.query.filter_by(name='user').first()
        if not user_role:
            # If role doesn't exist (rare), create it
            user_role = Roles(name='user', description='Regular user role')
            db.session.add(user_role)
            db.session.commit()

        new_user = User(
            name=data.get('username'),
            email=data.get('email'),
            password=generate_password_hash(data.get('password')),
            roles=[user_role]
        )
        db.session.add(new_user)
        db.session.commit()

        return {
            "message": "User registered successfully",
            "user": {
                "name": new_user.name,
                "email": new_user.email,
                "user_role": [r.name for r in new_user.roles][0]
            }
        }, 201

# ------------------------ Logout API ------------------------
class LogoutAPI(Resource):
    @jwt_required()
    def post(self):
        # JWT is stateless → frontend just discards the token
        return {"message": "User logged out successfully"}, 200
