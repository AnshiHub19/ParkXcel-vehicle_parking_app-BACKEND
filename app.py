from flask import Flask, jsonify
from flask_cors import CORS
from flask_restful import Api
from flask_security import Security
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
import os

from controllers.database import db
from controllers.config import Config
from controllers.user_datastore import user_datastore

# --------------------- App Factory ---------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS
    CORS(app)

    # Initialize DB
    db.init_app(app)

    # Initialize JWT
    JWTManager(app)

    # Initialize Flask-Security
    Security(app, user_datastore)

    # Initialize API
    api = Api(app)

    return app, api


# --------------------- DB Initialization ---------------------
from sqlalchemy import text

def init_db(app):
    with app.app_context():
        # 🔥 FORCE DROP old tables (one-time fix for Postgres)
        db.session.commit()
        
        db.create_all()

        # -------------------- Roles --------------------
        admin_role = user_datastore.find_or_create_role(
            'admin', description='Administrator role'
        )
        user_role = user_datastore.find_or_create_role(
            'user', description='Regular user role'
        )

        # -------------------- Admin User --------------------
        admin_user = user_datastore.find_user(email='adminmail@gmail.com')
        if not admin_user:
            admin_user = user_datastore.create_user(
                name='admin',
                email='adminmail@gmail.com',
                password=generate_password_hash('adminpss'),
                roles=[admin_role]
            )
        else:
            admin_user.password = generate_password_hash('adminpss')
            if admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)

        db.session.commit()
        print("Database initialized successfully.")


# --------------------- Create App ---------------------
app, api = create_app()
init_db(app)   # ✅ IMPORTANT: runs on Render also


# --------------------- Import API Resources ---------------------
from controllers.routes.authen_apis import LoginAPI, LogoutAPI, RegisterAPI
from controllers.routes.admin_apis import (
    ParkingLOTCreator, ParkingLOTViewer, ParkingLOTEditor, ParkingLOTDeleter,
    UserViewer, AdminDashSummary, Admin_AllBookings, AdminRevenue
)
from controllers.routes.user_apis import (
    User_ViewLots, User_ReserveSpot, User_ReleaseSpot,
    User_ParkHistory, User_Summary, User_CSVExport
)

# --------------------- Add Routes ---------------------
# Auth
api.add_resource(LoginAPI, '/api/login')
api.add_resource(LogoutAPI, '/api/logout')
api.add_resource(RegisterAPI, '/api/register')

# Admin
api.add_resource(ParkingLOTCreator, '/api/admin/create_lot')
api.add_resource(ParkingLOTViewer, '/api/admin/view_lots')
api.add_resource(ParkingLOTEditor, '/api/admin/edit_lot/<int:lot_id>')
api.add_resource(ParkingLOTDeleter, '/api/admin/delete_lot/<int:lot_id>')
api.add_resource(UserViewer, '/api/admin/view_users')
api.add_resource(AdminDashSummary, '/api/admin/summary')
api.add_resource(Admin_AllBookings, '/api/admin/bookings')
api.add_resource(AdminRevenue, '/api/admin/revenue_bylot')

# User
api.add_resource(User_ViewLots, '/api/user/view_lots')
api.add_resource(User_ReserveSpot, '/api/user/taking_spot')
api.add_resource(User_ReleaseSpot, '/api/user/leaving_spot')
api.add_resource(User_ParkHistory, '/api/user/booking_history')
api.add_resource(User_Summary, '/api/user/summary')
api.add_resource(User_CSVExport, '/api/user/export_csv')


# --------------------- Test / Celery Routes ---------------------
@app.route('/test-email')
def test_email():
    from tasks import send_daily_reminders
    task = send_daily_reminders.delay()
    return jsonify({
        'message': 'Email task queued successfully!',
        'task_id': task.id
    })


from tasks import sendparkingreminders, send_monthly_parking_report

@app.route("/test-daily-reminder")
def testdailyreminder():
    task = sendparkingreminders.delay()
    return {"message": "Daily reminder task queued!", "task_id": task.id}


@app.route("/test-monthly-report")
def testmonthlyreport():
    task = send_monthly_parking_report.delay()
    return {"message": "Monthly report task queued!", "task_id": task.id}


# --------------------- Run App ---------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)


