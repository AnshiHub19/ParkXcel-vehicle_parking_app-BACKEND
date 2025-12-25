from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.models import User


# ------------------------ Admin role required ------------------------
def admin_required(f):
    @wraps(f)
    @jwt_required()   # Flask-JWT-Extended authenticates token
    def decorated(*args, **kwargs):
        user_email = get_jwt_identity()  # Extract "sub" from JWT
        user = User.query.filter_by(email=user_email).first()

        if not user:
            return {"message": "User not found for this token"}, 401

        # Check role
        if "admin" not in [role.name for role in user.roles]:
            return {"message": "Admin role required"}, 403

        return f(*args, **kwargs)

    return decorated



# ------------------------ User role required ------------------------
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity as flask_get_jwt_identity
def user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()  # ensures a valid JWT is present
            user_email = flask_get_jwt_identity()
            user = User.query.filter_by(email=user_email).first()
            if not user or "user" not in [role.name for role in user.roles]:
                return {"message": "User role required"}, 403
            return f(*args, **kwargs)
        except Exception as e:
            return {"message": str(e)}, 401
    return decorated
