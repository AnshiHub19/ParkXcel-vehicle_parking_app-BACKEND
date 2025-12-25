from flask_restful import Resource
from flask import request, jsonify, make_response, send_file
from controllers.database import db
from controllers.models import User, ParkingLot, ParkingSpot, Reservation
from datetime import datetime
from controllers.auth_decorators import user_required
from flask_jwt_extended import jwt_required, get_jwt_identity
import csv
from io import StringIO


#from controllers.tasks import celery_app  # Uncomment if Celery setup is ready
#from flask_caching import Cache        # Optional caching integration

#------------------- View Available Lots -------------------
class User_ViewLots(Resource):
    @user_required
    def get(self):
        lots = ParkingLot.query.all()
        final_list = []
        for lot in lots:
            available_spots = sum(1 for s in lot.spots if s.current_status=="A")
            final_list.append({
                "lot_id": lot.id,
                "location_name": lot.location_name,
                "price": lot.price,
                "total_spots": lot.number_of_spots,
                "available_spots": available_spots
            })
        return {"parking_lots": final_list}, 200
class User_ReserveSpot(Resource):
    @user_required
    def post(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()

        data = request.get_json()
        lot_id = data.get("lot_id")
        if not lot_id:
            return {"message": "lot_id is required"}, 400

        # Pick the lowest available spot explicitly
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, current_status="A") \
                .order_by(ParkingSpot.id.asc()).first()

        if not spot:
            return {"message": "No available spots"}, 400

        reservation = Reservation(
            user_id=user.id,
            spot_id=spot.id,
            parking_time=datetime.utcnow(),
            current_status="active"
        )

        spot.current_status = "O"
        db.session.add(reservation)
        db.session.commit()

        return {
            "message": "Spot reserved successfully",
            "lot_id": lot_id,
            "spot_id": spot.id,
            "parking_time": reservation.parking_time.isoformat()
        }, 201

#-------------------------reserve spot
class User_ReserveSpot(Resource):
    @user_required
    def post(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()

        data = request.get_json()
        lot_id = data.get("lot_id")
        if not lot_id:
            return {"message": "lot_id is required"}, 400

        # pick lowest available spot in this lot
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, current_status="A") \
                                .order_by(ParkingSpot.id.asc()).first()

        if not spot:
            return {"message": "No available spots"}, 400

        # create reservation
        reservation = Reservation(
            user_id=user.id,
            spot_id=spot.id,
            parking_time=datetime.utcnow(),
            current_status="active"
        )
        spot.current_status = "O"
        db.session.add(reservation)
        db.session.commit()

        return {
            "message": "Spot reserved successfully",
            "lot_id": lot_id,
            "spot_number": spot.id,
            "parking_time": reservation.parking_time.isoformat()
        }, 201

#------------------- Release Spot -------------------
class User_ReleaseSpot(Resource):
    @user_required
    def post(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        data = request.get_json()
        spot_id = data.get("spot_id")
        if not spot_id:
            return {"message": "spot_id is required"}, 400

        reservation = Reservation.query.filter_by(
            user_id=user.id, spot_id=spot_id, current_status="active"
        ).first()
        if not reservation:
            return {"message": "No active reservation"}, 404

        reservation.exit_time = datetime.utcnow()
        reservation.current_status = "completed"

        spot = ParkingSpot.query.get(spot_id)
        lot = ParkingLot.query.get(spot.lot_id)
        duration_hours = (reservation.exit_time - reservation.parking_time).total_seconds() / 3600
        reservation.parking_cost = round(duration_hours * lot.price, 2)

        spot.current_status = "A"
        db.session.commit()

        return {
            "message": "Spot released successfully",
            "spot_id": spot_id,
            "exit_time": reservation.exit_time.isoformat(),
            "parking_cost": reservation.parking_cost
        }, 200


#------------------- Parking History -------------------
class User_ParkHistory(Resource):
    @user_required
    def get(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        reservations = Reservation.query.filter_by(user_id=user.id).order_by(Reservation.parking_time.desc()).all()
        history = []
        for res in reservations:
            spot = ParkingSpot.query.get(res.spot_id)
            lot = ParkingLot.query.get(spot.lot_id) if spot else None
            history.append({
                "reservation_id": res.id,
                "lot_name": lot.location_name if lot else None,
                "spot_id": spot.id if spot else None,
                "parking_time": res.parking_time.isoformat() if res.parking_time else None,
                "exit_time": res.exit_time.isoformat() if res.exit_time else None,
                "status": res.current_status,
                "parking_cost": res.parking_cost or 0
            })
        return {"parking_history": history}, 200


#------------------- Summary Charts -------------------
class User_Summary(Resource):
    @user_required
    def get(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        reservations = Reservation.query.filter_by(user_id=user.id).all()

        total_parks = len(reservations)
        total_hours = 0
        total_cost = 0
        lot_usage = {}

        for res in reservations:
            if res.exit_time:
                duration = (res.exit_time - res.parking_time).total_seconds() / 3600
                total_hours += duration
                total_cost += res.parking_cost
                spot = ParkingSpot.query.get(res.spot_id)
                lot = ParkingLot.query.get(spot.lot_id) if spot else None
                if lot:
                    lot_usage[lot.location_name] = lot_usage.get(lot.location_name, 0) + 1

        summary = {
            "total_parks": total_parks,
            "total_hours": round(total_hours, 2),
            "total_cost": round(total_cost, 2),
            "lot_usage": lot_usage
        }

        return summary, 200


#------------------- CSV Export -------------------
class User_CSVExport(Resource):
    @user_required
    def get(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        reservations = Reservation.query.filter_by(user_id=user.id).all()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Reservation ID", "Lot Name", "Spot ID", "Parking Time", "Exit Time", "Status", "Cost"])

        for res in reservations:
            spot = ParkingSpot.query.get(res.spot_id)
            lot = ParkingLot.query.get(spot.lot_id) if spot else None
            writer.writerow([
                res.id,
                lot.location_name if lot else "",
                spot.id if spot else "",
                res.parking_time.isoformat() if res.parking_time else "",
                res.exit_time.isoformat() if res.exit_time else "",
                res.current_status,
                res.parking_cost or 0
            ])

        output.seek(0)
        return send_file(output, mimetype="text/csv", attachment_filename="parking_history.csv", as_attachment=True)




