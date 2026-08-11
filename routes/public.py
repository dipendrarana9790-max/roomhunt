from flask import Blueprint, render_template, abort, session, request
from sqlalchemy import or_
from extensions import db
from models import Room, Interested

public = Blueprint("public", __name__)

# Root route (optional: redirect or render frontpage)
@public.route("/")
def home():
    rooms = Room.query.filter_by(
        approved=True,
        is_available=True
    ).order_by(Room.created_at.desc()).limit(6).all()
    return render_template("rooms.html", rooms=rooms)

# Main Rooms Search & Listing Route
@public.route("/rooms")
def rooms():
    # Retrieve query parameters from search form
    q = request.args.get("q", "").strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort_by = request.args.get("sort_by", "newest")

    # Base query: only list approved and available rooms
    query = Room.query.filter_by(approved=True, is_available=True)

    # Search keyword in title or address
    if q:
        search_filter = f"%{q}%"
        query = query.filter(
            or_(
                Room.title.ilike(search_filter),
                Room.address.ilike(search_filter)
            )
        )

    # Price range filters
    if min_price is not None:
        query = query.filter(Room.price >= min_price)
    if max_price is not None:
        query = query.filter(Room.price <= max_price)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(Room.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Room.price.desc())
    else:  # newest
        if hasattr(Room, "created_at"):
            query = query.order_by(Room.created_at.desc())
        else:
            query = query.order_by(Room.room_id.desc())

    rooms_list = query.all()

    return render_template(
        "rooms.html",
        rooms=rooms_list,
        search_query=q,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
    )

# Room Detail Route
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
    
    return render_template("room_detail.html", room=room, user_interest=user_interest)