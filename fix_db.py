from app import create_app
from controllers.database import db

print("🔧 Fixing Database...")
app, _ = create_app()

with app.app_context():
    db.create_all()
    print("ALL TABLES CREATED: users, roles, user_roles, parking_lots, parking_spots, RESERVATIONS")
    print("Admin user ready: adminmail@gmail.com / adminpss")
