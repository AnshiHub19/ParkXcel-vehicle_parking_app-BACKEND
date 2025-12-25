from celery_app import celery_app
from mail import send_mail
from sqlalchemy import create_engine, text
from datetime import date
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

# Set up Jinja2 environment
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

DB_PATH = "sqlite:///instance/parkxcel.db"

@celery_app.task(name="tasks.sendparkingreminders")
def sendparkingreminders():
    """Simple TEXT daily reminder sent to all active users."""
    engine = create_engine(DB_PATH)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT u.email, u.name FROM users u
            JOIN user_roles ur ON u.id=ur.user_id
            JOIN roles r ON ur.role_id=r.id
            WHERE r.name='user' AND u.active=1
        """))
        users = result.fetchall()

    today = date.today()
    sent_count = 0
    for email, name in users:
        body = f"""PARKXCEL DAILY PARKING REMINDER

Hi {name},

Don't forget to book your parking spot for today ({today.strftime('%d %b %Y')})!

Book YOUR SPOT NOW!

ParkXcel Team 💙
"""
        try:
            send_mail(email, f"Daily Reminder - {today.strftime('%d %b')}", body)
            sent_count += 1
            print(f" Sent to {name}")
        except Exception as e:
            print(f" Failed to send to {name}: {e}")
    
    return f" {sent_count} daily reminders sent!"

@celery_app.task(name="tasks.send_monthly_parking_report")
def send_monthly_parking_report():
    """HTML monthly report sent to all active users."""
    engine = create_engine(DB_PATH)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT u.email, u.name FROM users u
            JOIN user_roles ur ON u.id=ur.user_id
            JOIN roles r ON ur.role_id=r.id
            WHERE r.name='user' AND u.active=1
        """))
        users = result.fetchall()
    
    template = env.get_template('monthly_report.html')
    sent_count = 0
    for email, name in users:
        # Fill template variables here as needed or static placeholders
        html_body = template.render(
            user_name=name,
            month_year=date.today().strftime('%B %Y'),
            total_bookings=10,
            total_amount=1500,
            most_used_lot="Central Mall"
        )
        try:
            send_mail(email, f"📊 Monthly Parking Report - {date.today().strftime('%B %Y')}", html_body)
            sent_count += 1
            print(f" Monthly report sent to {name}")
        except Exception as e:
            print(f" Failed monthly report to {name}: {e}")
    
    return f" {sent_count} monthly reports sent!"
