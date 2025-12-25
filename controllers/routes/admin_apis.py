from flask_restful import Resource
from flask import request, jsonify
from controllers.database import db
from controllers.models import User, ParkingLot, ParkingSpot, Reservation
from controllers.auth_decorators import admin_required
from datetime import datetime

#------------------- Create Parking Lot -------------------
class ParkingLOTCreator(Resource):
    @admin_required
    def post(self):
        data = request.get_json()
        required_fields = ["location_name", "price", "pin_code", "number_of_spots"]
        for field in required_fields:
            if field not in data:
                return {"message": f"{field} is required"}, 400

        lot = ParkingLot(
            location_name=data["location_name"],
            price=data["price"],
            pin_code=data["pin_code"],
            number_of_spots=data["number_of_spots"]
        )
        db.session.add(lot)
        db.session.commit()

        # Automatically create spots
        for _ in range(lot.number_of_spots):
            spot = ParkingSpot(lot_id=lot.id, current_status="A")
            db.session.add(spot)
        db.session.commit()

        return {
            "message": "Parking lot created successfully",
            "lot_id": lot.id,
            "spots_created": lot.number_of_spots
        }, 201


#------------------- View All Lots -------------------
class ParkingLOTViewer(Resource):
    @admin_required
    def get(self):
        lots = ParkingLot.query.all()
        lot_list = []
        for lot in lots:
            total_spots = len(lot.spots)
            available = sum(1 for s in lot.spots if s.current_status == "A")
            occupied = total_spots - available
            lot_list.append({
                "lot_id": lot.id,
                "location_name": lot.location_name,
                "price": lot.price,
                "total_spots": total_spots,
                "available_spots": available,
                "occupied_spots": occupied,
                "spots": [{"spot_id": s.id, "status": "Available" if s.current_status=="A" else "Occupied"} for s in lot.spots]
            })
        return {"parking_lots": lot_list}, 200


#------------------- Edit Lot -------------------
class ParkingLOTEditor(Resource):
    @admin_required
    def put(self, lot_id):
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return {"message": "Parking lot not found"}, 404

        data = request.get_json()
        if "location_name" in data:
            lot.location_name = data["location_name"]
        if "price" in data:
            lot.price = float(data["price"])
        if "pin_code" in data:
            lot.pin_code = data["pin_code"]

        if "number_of_spots" in data:
            new_count = data["number_of_spots"]
            old_count = lot.number_of_spots
            if new_count > old_count:
                for _ in range(new_count - old_count):
                    db.session.add(ParkingSpot(lot_id=lot.id, current_status="A"))
            elif new_count < old_count:
                available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, current_status="A").all()
                if len(available_spots) < (old_count - new_count):
                    return {"message": "Cannot reduce spots; some are occupied"}, 400
                for spot in available_spots[:old_count - new_count]:
                    db.session.delete(spot)
            lot.number_of_spots = new_count

        db.session.commit()
        return {"message": "Parking lot updated successfully", "lot_id": lot.id}, 200


#------------------- Delete Lot -------------------
class ParkingLOTDeleter(Resource):
    @admin_required
    def delete(self, lot_id):
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return {"message": "Parking lot not found"}, 404

        # Check if any spot is occupied
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, current_status="O").count()
        if occupied_spots > 0:
            return {"message": "Cannot delete lot, some spots are occupied"}, 400

        try:
            ParkingSpot.query.filter_by(lot_id=lot.id).delete()
            db.session.delete(lot)
            db.session.commit()
            return {"message": "Parking lot deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            return {"message": "Error deleting lot", "error": str(e)}, 500


#------------------- View All Users -------------------
class UserViewer(Resource):
    @admin_required
    def get(self):
        users = User.query.all()
        result = []
        for u in users:
            active_res = Reservation.query.filter_by(user_id=u.id, current_status="active").first()
            if active_res:
                spot = ParkingSpot.query.get(active_res.spot_id)
                lot = ParkingLot.query.get(spot.lot_id) if spot else None
                user_info = {
                    "user_id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "roles": [r.name for r in u.roles],
                    "current_status": "Parked",
                    "current_lot": lot.location_name if lot else None,
                    "current_spot": spot.id if spot else None,
                    "parking_since": active_res.parking_time.isoformat() if active_res.parking_time else None
                }
            else:
                user_info = {
                    "user_id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "roles": [r.name for r in u.roles],
                    "current_status": "Not parked",
                    "current_lot": None,
                    "current_spot": None,
                    "parking_since": None
                }
            result.append(user_info)
        return {"users": result}, 200


#------------------- Admin Summary -------------------
class AdminDashSummary(Resource):
    @admin_required
    def get(self):
        lots = ParkingLot.query.all()
        total_lots = len(lots)
        total_spots = sum(l.number_of_spots for l in lots)
        occupied_spots = sum(1 for l in lots for s in l.spots if s.current_status == "O")
        available_spots = total_spots - occupied_spots

        # Active users (currently parked)
        active_users = Reservation.query.filter_by(current_status="active").count()

        # Total users
        total_users = User.query.count()

        # Total revenue calculation
        completed_res = Reservation.query.filter_by(current_status="completed").all()
        total_revenue = sum(r.parking_cost for r in completed_res if r.parking_cost)

        summary = {
            "total_lots": total_lots,
            "total_spots": total_spots,
            "occupied_spots": occupied_spots,
            "available_spots": available_spots,
            "active_users": active_users,
            "total_users": total_users,
            "total_revenue": round(total_revenue, 2)
        }

        return summary, 200


#------------------- All Parking Records -------------------
class Admin_AllBookings(Resource):
    @admin_required
    def get(self):
        reservations = Reservation.query.order_by(Reservation.parking_time.desc()).all()
        all_records = []
        for res in reservations:
            user = User.query.get(res.user_id)
            spot = ParkingSpot.query.get(res.spot_id)
            lot = ParkingLot.query.get(spot.lot_id) if spot else None
            all_records.append({
                "reservation_id": res.id,
                "user_name": user.name if user else None,
                "user_email": user.email if user else None,
                "lot_name": lot.location_name if lot else None,
                "spot_id": spot.id if spot else None,
                "parking_time": res.parking_time.isoformat() if res.parking_time else None,
                "exit_time": res.exit_time.isoformat() if res.exit_time else None,
                "status": res.current_status,
                "parking_cost": res.parking_cost or 0
            })
        return {"all_reservations": all_records}, 200
    
    #-----------------------revenue
class AdminRevenue(Resource):
    @admin_required
    def get(self):
        lots = ParkingLot.query.all()
        revenue_data = []

        for lot in lots:
            # Sum revenue of all completed reservations for this lot
            total_revenue = (
                db.session.query(db.func.sum(Reservation.parking_cost))
                .join(ParkingSpot, ParkingSpot.id == Reservation.spot_id)
                .filter(ParkingSpot.lot_id == lot.id)
                .filter(Reservation.current_status == "completed")
                .scalar()
            ) or 0

            revenue_data.append({
                "lot_name": lot.location_name,
                "revenue": round(total_revenue, 2)
            })

        return {"revenue_by_lot": revenue_data}, 200

