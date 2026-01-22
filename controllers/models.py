from datetime import datetime
from controllers.database import db
from flask_security import UserMixin, RoleMixin, Security, UserDatastore         #clssed have predefinied methods which r necessary to retrieve authenticatn token
import uuid


'''----------------------------------USER AND ROLE MODELS FOR FLASK SECURITY AUTHENTICATION----------------------------------'''
class User(db.Model,UserMixin):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(200),unique=True,nullable=False)
    password = db.Column(db.Text, nullable=False)
    active=db.Column(db.Boolean(),default=True)

    fs_uniquifier=db.Column(db.String(250),unique=True,nullable=False, default=lambda: str(uuid.uuid4()))
    fs_token_uniquifier=db.Column(db.String(250),unique=True,nullable=False, default=lambda: str(uuid.uuid4()))
    roles=db.relationship('Roles',secondary='user_roles',backref=db.backref('users',lazy='dynamic'))
    reservations = db.relationship("Reservation", backref="user", lazy=True)


class Roles(db.Model,RoleMixin):
    __tablename__='roles'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),unique=True,nullable=False)
    description=db.Column(db.String(200),nullable=False)


class UserRoles(db.Model):
    __tablename__='user_roles'
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'),nullable=False)


'''----------------------------------PARKING LOT, SPOT AND RESERVATION MODELS----------------------------------'''

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    number_of_spots = db.Column(db.Integer, nullable=False)

    # Relationship to spots
    spots = db.relationship("ParkingSpot", backref="lot", lazy=True)



class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'

    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    
    current_status = db.Column(db.String(1), default='A')      # A = Available, O = Occupied

    # Relationship to reservations
    reservations = db.relationship("Reservation", backref="spot", lazy=True)



class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)

    parking_time = db.Column(db.DateTime, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime)

    parking_cost = db.Column(db.Float, default=0.0)

    current_status = db.Column(db.String(20), default="active")
    # active → parked right now
    # completed → left the parking
