class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///parkxcel.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'parknirvanasecretkey'
    SECURITY_PASSWORD_SALT = 'parknirvanasalt'

    # Flask-Security password hashing
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha256'
    SECURITY_PASSWORD_SINGLE_HASH = False
    SECURITY_JOIN_USER_ROLES = 'user_roles'

    # JWT config – make this the same as SECRET_KEY
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

    # Redis
    REDIS_URL = "redis://localhost:6380/0"

    # Celery
    broker_url = "redis://localhost:6380/0"
    result_backend = "redis://localhost:6380/0"


    # Mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'anshikaagg27@gmail.com'
    MAIL_PASSWORD = 'Anshika@1080'
