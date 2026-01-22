import os

class Config:
    # =======================
    # Database (Render + Local)
    # =======================
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///parkxcel.db"   # fallback only for local
    )

    # Render postgres fix
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # =======================
    # Security
    # =======================
    SECRET_KEY = os.getenv("SECRET_KEY", "parknirvanasecretkey")
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "parknirvanasalt")

    SECURITY_PASSWORD_HASH = "pbkdf2_sha256"
    SECURITY_PASSWORD_SINGLE_HASH = False
    SECURITY_JOIN_USER_ROLES = "user_roles"

    # =======================
    # JWT
    # =======================
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

    # =======================
    # Redis + Celery
    # =======================
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")

    broker_url = REDIS_URL
    result_backend = REDIS_URL

    # =======================
    # Mail (Environment only)
    # =======================
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
