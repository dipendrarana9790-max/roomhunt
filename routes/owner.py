from flask import Blueprint, render_template, request, redirect, session, url_for, current_app, flash
from werkzeug.utils import secure_filename
from extensions import db
from models import Owner, Room, Interested, User
from sqlalchemy.orm import joinedload
from sqlalchemy import asc
import os
import uuid

owner = Blueprint("owner", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def owner_required():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "owner":
        return "Access Denied!", 403

    return None

def generate_unique_filename(filename):
    ext = os.path.splitext(secure_filename(filename))[1]
    return f"{uuid.uuid4().hex}{ext}"

@owner.route("/owner")
def owner_dashboard():
    access = owner_required()
    if access:
        return access

    current_user_id = session.get("user_id")
    owner_profile = Owner.query.filter_by(user_id=current_user_id).first()

    if not owner_profile:
        stats = {
            "total_rooms": 0,
            "available_rooms": 0,
            "pending_approval": 0,
            "pending_interests": 0,
            "accepted_interests": 0,
            "occupancy_rate": 0,
        }
        return render_template("owner_dashboard.html", stats=stats, recent_inquiries=[], recent_rooms=[])

    owner_id = owner_profile.owner_id

    # Core Stats Queries
    total_rooms = Room.query.filter_by(owner_id=owner_id).count()
    
    available_rooms = Room.query.filter_by(
        owner_id=owner_id, 
        approved=True, 
        is_available=True
    ).count()

    pending_approval = Room.query.filter_by(
        owner_id=owner_id, 
        approved=False
    ).count()

    pending_interests = (
        Interested.query
        .join(Room)
        .filter(Room.owner_id == owner_id, Interested.status == "pending")
        .count()
    )

    accepted_interests = (
        Interested.query
        .join(Room)
        .filter(Room.owner_id == owner_id, Interested.status == "accepted")
        .count()
    )

    # Calculate Occupancy/Accepted Rate
    occupancy_rate = round((accepted_interests / total_rooms * 100)) if total_rooms > 0 else 0

    stats = {
        "total_rooms": total_rooms,
        "available_rooms": available_rooms,
        "pending_approval": pending_approval,
        "pending_interests": pending_interests,
        "accepted_interests": accepted_interests,
        "occupancy_rate": occupancy_rate,
    }

    # Fetch 5 Most Recent Tenant Inquiries
    recent_inquiries = (
        Interested.query
        .join(Room)
        .filter(Room.owner_id == owner_id)
        .order_by(Interested.interested_at.desc())
        .limit(5)
        .all()
    )

    # Fetch 4 Most Recent Property Listings
    recent_rooms = (
        Room.query
        .filter_by(owner_id=owner_id)
        .order_by(Room.created_at.desc())
        .limit(4)
        .all()
    )

    return render_template(
        "owner_dashboard.html", 
        stats=stats, 
        recent_inquiries=recent_inquiries,
        recent_rooms=recent_rooms
    )

@owner.route("/owner/profile", methods=["GET", "POST"])
def owner_profile():
    access = owner_required()
    if access:
        return access

    current_user_id = session.get("user_id")
    user = User.query.get_or_404(current_user_id)
    
    # Get or create the Owner profile record
    owner = Owner.query.filter_by(user_id=current_user_id).first()
    if not owner:
        owner = Owner(user_id=current_user_id)
        db.session.add(owner)
        db.session.commit()

    if request.method == "POST":
        # 1. Update basic info
        user.fullname = request.form.get("fullname", user.fullname).strip()
        user.phone = request.form.get("phone", user.phone).strip()
        owner.contact = request.form.get("contact", owner.contact).strip()
        owner.address = request.form.get("address", owner.address).strip()
        owner.citizenship_no = request.form.get("citizenship_no", owner.citizenship_no).strip()

        # 2. File Upload Directory
        upload_folder = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_folder, exist_ok=True)

        # Helper function for file uploads
        def save_uploaded_file(file_key, old_filename):
            file = request.files.get(file_key)
            if file and file.filename != "" and allowed_file(file.filename):
                filename = secure_filename(f"owner_{user.id}_{file_key}_{file.filename}")
                file.save(os.path.join(upload_folder, filename))
                return filename
            return old_filename

        # 3. Process image uploads
        owner.profile_photo = save_uploaded_file("profile_photo", owner.profile_photo)
        owner.citizenship_photo = save_uploaded_file("citizenship_photo", owner.citizenship_photo)
        owner.citizenship_back_photo = save_uploaded_file("citizenship_back_photo", owner.citizenship_back_photo)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("owner.owner_profile"))

    return render_template("owner_profile.html", user=user, owner=owner)

@owner.route("/add-room", methods=["GET", "POST"])
def add_room():
    access = owner_required()
    if access:
        return access

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        price = request.form["price"]
        address = request.form["address"]
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]
        image = request.files["room_image"]

        filename = secure_filename(image.filename)
        image.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))

        # Find owner profile from the logged-in user's ID
        owner_record = Owner.query.filter_by(user_id=session["user_id"]).first()

        if owner_record is None:
            return "Owner not found."

        # Create new Room object instance
        new_room = Room(
            owner_id=owner_record.owner_id,
            title=title,
            description=description,
            price=price,
            address=address,
            latitude=latitude,
            longitude=longitude,
            room_image=filename
        )

        # Add and save to database
        db.session.add(new_room)
        db.session.commit()

        return redirect("/owner")

    return render_template("add_room.html")


@owner.route("/my-rooms")
def rooms():
    access = owner_required()
    if access:
        return access

    # Find owner profile from the logged-in user's ID
    owner_record = Owner.query.filter_by(user_id=session["user_id"]).first()

    if owner_record is None:
        return "Owner not found."

    # Fetch only this owner's rooms sorted by creation timestamp descending
    my_rooms = Room.query.filter_by(owner_id=owner_record.owner_id)\
                         .order_by(Room.created_at.desc())\
                         .all()

    return render_template(
        "owner_rooms.html",
        rooms=my_rooms
    )
    
@owner.route("/edit-room/<int:id>", methods=["GET", "POST"])
def edit_room(id):
    access = owner_required()
    if access:
        return access

    owner_record = Owner.query.filter_by(user_id=session["user_id"]).first()
    if not owner_record:
        return "Owner profile not found.", 404

    # Query using room_id
    room = Room.query.filter_by(room_id=id, owner_id=owner_record.owner_id).first_or_404()

    if request.method == "POST":
        room.title = request.form.get("title")
        room.description = request.form.get("description")
        room.price = request.form.get("price")
        room.address = request.form.get("address")
        room.latitude = request.form.get("latitude")
        room.longitude = request.form.get("longitude")

        image = request.files.get("room_image")
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            room.room_image = filename

        db.session.commit()
        return redirect(url_for("owner.rooms"))

    return render_template("owner_room_edit.html", room=room)
@owner.route("/delete-room/<int:id>", methods=["GET", "POST"])
def delete_room(id):
    access = owner_required()
    if access:
        return access

    owner_record = Owner.query.filter_by(user_id=session["user_id"]).first()
    if not owner_record:
        return "Owner profile not found.", 404

    # Fetch room by primary key room_id
    room = Room.query.filter_by(room_id=id, owner_id=owner_record.owner_id).first_or_404()

    db.session.delete(room)
    db.session.commit()

    return redirect(url_for("owner.rooms"))

@owner.route("/owner/interested-users")
def interested_users():
    access = owner_required()
    if access:
        return access

    current_user_id = session.get("user_id")
    owner_profile = Owner.query.filter_by(user_id=current_user_id).first()

    if not owner_profile:
        flash("Owner profile not found.", "danger")
        return redirect(url_for("public.index"))

    # Fetch rooms owned by this user, eager-loading interests sorted by submission date (FIFO)
    rooms = (
        Room.query
        .options(joinedload(Room.interests).joinedload(Interested.user))
        .filter(Room.owner_id == owner_profile.owner_id)
        .all()
    )

    # Sort each room's interests in Python to ensure correct queue order (Oldest first)
    for room in rooms:
        room.interests.sort(key=lambda x: x.interested_at)

    return render_template("interested_users.html", rooms=rooms)

@owner.route("/owner/interest/<int:interest_id>/update-status", methods=["POST"])
def update_interest_status(interest_id):
    access = owner_required()
    if access:
        return access

    action = request.form.get("action")  # 'accepted' or 'rejected'
    if action not in ["accepted", "rejected"]:
        flash("Invalid action.", "danger")
        return redirect(url_for("owner.interested_users"))

    interest = Interested.query.get_or_404(interest_id)

    # Check ownership
    current_user_id = session.get("user_id")
    owner_profile = Owner.query.filter_by(user_id=current_user_id).first()

    if not owner_profile or interest.room.owner_id != owner_profile.owner_id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("owner.interested_users"))

    # STRICT FIFO VALIDATION: Check if this is the earliest pending request for this room
    earliest_pending = (
        Interested.query
        .filter_by(room_id=interest.room_id, status="pending")
        .order_by(Interested.interested_at.asc())
        .first()
    )

    if earliest_pending and earliest_pending.interest_id != interest.interest_id:
        flash("You must process (accept or reject) earlier pending applicants first.", "warning")
        return redirect(url_for("owner.interested_users"))

    if action == "accepted":
        # Accept current applicant
        interest.status = "accepted"

        # REMOVED: interest.room.is_available = False 
        # Room listing stays visible on the public platform even when accepted.

    elif action == "rejected":
        # Reject current applicant
        interest.status = "rejected"

    db.session.commit()

    flash(f"User request updated to {action}.", "success")
    return redirect(url_for("owner.interested_users"))