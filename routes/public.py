from flask import Blueprint, render_template, abort, session
from extensions import db
from models import Room, Interested

public = Blueprint("public", __name__)

@public.route("/")
def rooms():
    rooms = Room.query.filter_by(
        approved=True,
        is_available=True
    ).order_by(Room.created_at.desc()).all()
    return render_template("rooms.html", rooms=rooms)

@public.route("/room/<int:room_id>")
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    
    if not room.approved:
        abort(404)
    
    # Get user's interest if logged in
    user_interest = None
    if "user_id" in session:
        user_interest = Interested.query.filter_by(
            room_id=room_id,
            user_id=session["user_id"]
        ).first()
        print(f"User interest for room {room_id}: {user_interest}")  # Debug
    
    return render_template("room_detail.html", room=room, user_interest=user_interest)