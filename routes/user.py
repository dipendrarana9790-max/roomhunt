import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, session, current_app, flash, url_for
from werkzeug.utils import secure_filename
from extensions import db
from models import Owner, User, Interested, Room

user = Blueprint("user", __name__)

def generate_unique_filename(filename):
    """Utility to generate a unique filename using UUID to prevent collisions."""
    ext = os.path.splitext(secure_filename(filename))[1]
    return f"{uuid.uuid4().hex}{ext}"

@user.route("/owner-form", methods=["GET", "POST"])
def become_owner():
    # 1. Require user to be logged in
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # 2. Check if the user already submitted an application
    existing_owner = Owner.query.filter_by(user_id=session["user_id"]).first()
    if existing_owner:
        flash("You have already submitted an owner application.", "info")
        return redirect(url_for("public.rooms"))

    if request.method == "POST":
        # Extract form fields
        citizenship_no = request.form.get("citizenship_no")
        contact = request.form.get("contact")
        address = request.form.get("address")

        # Extract files
        citizenship_photo = request.files.get("citizenship_photo")
        citizenship_back_photo = request.files.get("citizenship_back_photo")
        profile_photo = request.files.get("profile_photo")

        # Basic File Presence Check
        if not (citizenship_photo and citizenship_back_photo and profile_photo):
            flash("Please upload all required photos.", "danger")
            return redirect(request.url)

        # Generate unique secure filenames
        cit_front_filename = generate_unique_filename(citizenship_photo.filename)
        cit_back_filename = generate_unique_filename(citizenship_back_photo.filename)
        profile_filename = generate_unique_filename(profile_photo.filename)

        # Ensure upload folder exists
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        # Save files to UPLOAD_FOLDER
        citizenship_photo.save(os.path.join(upload_folder, cit_front_filename))
        citizenship_back_photo.save(os.path.join(upload_folder, cit_back_filename))
        profile_photo.save(os.path.join(upload_folder, profile_filename))

        # Create new Owner record
        new_owner_request = Owner(
            user_id=session["user_id"],
            citizenship_no=citizenship_no,
            contact=contact,
            address=address,
            citizenship_photo=cit_front_filename,
            citizenship_back_photo=cit_back_filename,
            profile_photo=profile_filename,
            approved=False,
            applied_at=datetime.utcnow()
        )

        db.session.add(new_owner_request)
        db.session.commit()

        flash("Your application to become an owner has been submitted and is pending verification.", "success")
        return redirect(url_for("public.rooms"))

    return render_template("owner_form.html")

# Add this route to your existing 'user' blueprint
@user.route("/room/<int:room_id>/interest", methods=["POST"])
def express_interest(room_id):
    print("=" * 50)
    print(f"EXPRESS INTEREST CALLED for room {room_id}")
    print(f"Session: {dict(session)}")
    print(f"Form data: {dict(request.form)}")
    
    # 1. Require user authentication
    if "user_id" not in session:
        print("User not logged in")
        flash("Please log in to express interest in this room.", "warning")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    print(f"User ID: {user_id}")
    
    # 2. Fetch room and verify existence & availability
    room = Room.query.get_or_404(room_id)
    print(f"Room: {room.title}, Available: {room.is_available}, Approved: {room.approved}")
    
    if not room.is_available or not room.approved:
        print("Room not available or not approved")
        flash("This room is currently not available for booking.", "danger")
        return redirect(url_for("public.room_detail", room_id=room_id))

    # 3. Prevent owners from expressing interest in their own listings
    if room.owner and room.owner.user_id == user_id:
        print("User is the owner of this room")
        flash("You cannot express interest in your own room listing.", "danger")
        return redirect(url_for("public.room_detail", room_id=room_id))

    # 4. Check if user has already expressed interest
    existing_interest = Interested.query.filter_by(room_id=room_id, user_id=user_id).first()
    if existing_interest:
        print(f"Existing interest found: {existing_interest.status}")
        flash("You have already expressed interest in this room.", "info")
        return redirect(url_for("public.room_detail", room_id=room_id))

    # 5. Extract form data
    message = request.form.get("message", "").strip()
    print(f"Message: {message}")
    
    # 6. Save new interest entry
    try:
        new_interest = Interested(
            room_id=room_id,
            user_id=user_id,
            message=message or None,
            status='pending'
        )
        db.session.add(new_interest)
        db.session.commit()
        print(f"✅ Interest created successfully! ID: {new_interest.interest_id}")
        flash("Your interest has been submitted to the property owner!", "success")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating interest: {str(e)}")
        flash("An error occurred while submitting your interest. Please try again.", "danger")

    print("=" * 50)
    return redirect(url_for("public.room_detail", room_id=room_id))

@user.route("/my-interests")
def my_interests():
    if "user_id" not in session:
        flash("Please log in to view your expressed interests.", "warning")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # Retrieve all interest requests made by the logged-in user
    user_interests = (
        Interested.query.filter_by(user_id=user_id)
        .order_by(Interested.interested_at.desc())
        .all()
    )

    # Calculate the queue position for pending requests per room
    queue_positions = {}
    for interest in user_interests:
        if interest.status == "pending":
            # Count how many pending requests for this specific room were submitted 
            # at or before this request's creation timestamp
            position = (
                Interested.query.filter_by(room_id=interest.room_id, status="pending")
                .filter(Interested.interested_at <= interest.interested_at)
                .count()
            )
            queue_positions[interest.interest_id] = position

    return render_template(
        "my_interests.html",
        user_interests=user_interests,
        queue_positions=queue_positions,
    )
    if "user_id" not in session:
        flash("Please log in to view your expressed interests.", "warning")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # Query all interest records for the logged-in user ordered by most recent
    user_interests = (
        Interested.query.filter_by(user_id=user_id)
        .order_by(Interested.interested_at.desc())
        .all()
    )

    # Calculate queue position for each pending interest
    for interest in user_interests:
        if interest.status == 'pending':
            # Count how many pending requests were submitted BEFORE or AT the same time for this room
            queue_position = Interested.query.filter(
                Interested.room_id == interest.room_id,
                Interested.status == 'pending',
                Interested.interested_at <= interest.interested_at
            ).count()
            interest.queue_position = queue_position
        else:
            interest.queue_position = None

    return render_template("my_interests.html", user_interests=user_interests)