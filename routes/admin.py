from flask import Blueprint, render_template, redirect, url_for, session
from extensions import db
from models import User, Owner, Room, Interested
from sqlalchemy import func, extract
from datetime import datetime

admin = Blueprint("admin", __name__)


# Check Admin Access
def check_admin():
    # User not logged in
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # User is not admin
    if session.get("role") != "admin":
        return "Access Denied!", 403

    return None


# Admin Dashboard
# @admin.route("/admin")
# def admin_dashboard():
#     access = check_admin()
#     if access:
#         return access

#     # Performs an INNER JOIN on Owners and Users tables
#     owners = db.session.query(Owner, User).join(User, Owner.user_id == User.id).all()

#     return render_template("admin_dashboard.html", owners=owners)

@admin.route("/admin/dashboard")
def admin_dashboard():
    access = check_admin()  # Your admin authentication check
    if access:
        return access

    # Dynamic counts from database
    total_users = User.query.filter_by(role='user').count()
    total_owners = Owner.query.count()
    total_rooms = Room.query.count()
    
    # Unapproved room listings awaiting verification
    pending_rooms = Room.query.filter_by(approved=False).count()
    
    # Unapproved owner KYC applications
    pending_owners = Owner.query.filter_by(approved=False).count()
    
    # Combined pending requests count
    total_pending_requests = pending_rooms + pending_owners

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_owners=total_owners,
        total_rooms=total_rooms,
        pending_requests=total_pending_requests,
        pending_rooms=pending_rooms,
        pending_owners=pending_owners
    )
# View All Users
@admin.route("/admin/users")
def all_users():
    access = check_admin()
    if access:
        return access

    # Fetch all users
    users = User.query.all()

    return render_template("all_users.html", users=users)

@admin.route("/admin/user/<int:user_id>")
def user_details(user_id):
    access = check_admin()
    if access:
        return access

    user = User.query.get_or_404(user_id)
    return render_template("admin_user.html", user=user)

# routes/admin.py

@admin.route('/toggle_status/<int:user_id>')
def toggle_user_status(user_id):
    # Your logic to block/unblock the user
    user = User.query.get_or_404(user_id)
    user.isactive = not user.isactive
    db.session.commit()
    return redirect(url_for('admin.all_users'))

# Approve Owner
@admin.route("/approve-owner/<int:owner_id>")
def approve_owner(owner_id):
    access = check_admin()
    if access:
        return access

    # Get the owner record by its primary key
    owner_record = Owner.query.get(owner_id)

    if owner_record:
        # Update owner approval status
        owner_record.approved = True
        
        # Access the mapped User record directly via the backref relationship
        user_record = owner_record.user
        if user_record:
            user_record.role = 'owner'

        # Commit changes for both records in a single transaction
        db.session.commit()

    return redirect(url_for("admin.admin_dashboard"))


# View Pending Owner Requests
@admin.route("/admin/owners")
def owners():
    # Protect admin route
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    # Fetch unapproved owners joined with their user details
    requests = db.session.query(Owner, User).join(User, Owner.user_id == User.id).filter(Owner.approved == False).all()

    return render_template("owner_request.html", requests=requests)


# Reject Owner
@admin.route("/reject-owner/<int:owner_id>")
def reject_owner(owner_id):
    access = check_admin()
    if access:
        return access

    owner_record = Owner.query.get(owner_id)
    
    if owner_record:
        # Delete the application record
        db.session.delete(owner_record)
        db.session.commit()

    return redirect(url_for("admin.owners"))

#delete user
@admin.route("/admin/delete-user/<int:user_id>")
def delete_user(user_id):
    access = check_admin()
    if access:
        return access

    user_record = User.query.get(user_id)

    # CRITICAL BACKEND CHECK: Prevent deleting admin accounts
    if user_record and user_record.role != 'admin':
        db.session.delete(user_record)
        db.session.commit()
    elif user_record and user_record.role == 'admin':
        return "Cannot delete an administrator account!", 400

    return redirect(url_for("admin.all_users"))

# View All Rooms (Joined with Owner and User details)
@admin.route("/admin/rooms")
def admin_rooms():
    access = check_admin()
    if access:
        return access

    rooms = db.session.query(Room, Owner, User)\
        .join(Owner, Room.owner_id == Owner.owner_id)\
        .join(User, Owner.user_id == User.id)\
        .order_by(Room.created_at.asc())\
        .all()

    return render_template("admin_rooms.html", rooms=rooms)

# Toggle Room Approval Status (Verify / Unverify)
@admin.route("/admin/toggle-approve-room/<int:room_id>")
def toggle_approve_room(room_id):
    access = check_admin()
    if access:
        return access

    room_record = Room.query.get_or_404(room_id)
    # Toggle approval boolean status
    room_record.approved = not room_record.approved
    db.session.commit()

    return redirect(url_for("admin.admin_rooms"))

# Delete Room Listing
@admin.route("/admin/delete-room/<int:room_id>")
def delete_room(room_id):
    access = check_admin()
    if access:
        return access

    room_record = Room.query.get_or_404(room_id)
    db.session.delete(room_record)
    db.session.commit()

    return redirect(url_for("admin.admin_rooms"))

# admin admin_report
@admin.route("/admin/reports")
def admin_report():
    access = check_admin()
    if access:
        return access

    # ---------------------------------------------------------
    # 1. USER METRICS
    # ---------------------------------------------------------
    total_users = User.query.count()
    active_users = User.query.filter_by(isactive=True).count()
    blocked_users = User.query.filter_by(isactive=False).count()
    verified_users = User.query.filter_by(isverified=True).count()

    regular_users = User.query.filter_by(role='user').count()
    owner_users = User.query.filter_by(role='owner').count()
    admin_users = User.query.filter_by(role='admin').count()

    # ---------------------------------------------------------
    # 2. OWNER & KYC METRICS
    # ---------------------------------------------------------
    total_owners = Owner.query.count()
    approved_owners = Owner.query.filter_by(approved=True).count()
    pending_owners = Owner.query.filter_by(approved=False).count()

    # ---------------------------------------------------------
    # 3. ROOM & FINANCIAL METRICS
    # ---------------------------------------------------------
    total_rooms = Room.query.count()
    approved_rooms = Room.query.filter_by(approved=True).count()
    pending_rooms = Room.query.filter_by(approved=False).count()
    available_rooms = Room.query.filter_by(is_available=True, approved=True).count()
    occupied_rooms = Room.query.filter_by(is_available=False).count()

    # Pricing Statistics
    avg_price = db.session.query(func.avg(Room.price)).scalar() or 0.0
    max_price = db.session.query(func.max(Room.price)).scalar() or 0.0
    min_price = db.session.query(func.min(Room.price)).scalar() or 0.0
    total_inventory_value = db.session.query(func.sum(Room.price)).scalar() or 0.0

    # ---------------------------------------------------------
    # 4. BOOKING / INTEREST REQUEST METRICS
    # ---------------------------------------------------------
    total_interests = Interested.query.count()
    pending_interests = Interested.query.filter_by(status='pending').count()
    accepted_interests = Interested.query.filter_by(status='accepted').count()
    rejected_interests = Interested.query.filter_by(status='rejected').count()

    # Income Calculations
    # Estimated Active Platform Value from Accepted Rentals
    total_accepted_revenue = db.session.query(func.sum(Room.price))\
        .join(Interested, Room.room_id == Interested.room_id)\
        .filter(Interested.status == 'accepted')\
        .scalar() or 0.0

    # Estimated Admin Platform Fee (e.g., 10% commission model - adjust as needed)
    platform_commission_rate = 0.10  # 10%
    estimated_admin_earnings = float(total_accepted_revenue) * platform_commission_rate

    # ---------------------------------------------------------
    # 5. RECENT ACTIVITY LISTINGS (Top 5)
    # ---------------------------------------------------------
    recent_rooms = db.session.query(Room, User)\
        .join(Owner, Room.owner_id == Owner.owner_id)\
        .join(User, Owner.user_id == User.id)\
        .order_by(Room.created_at.desc())\
        .limit(5)\
        .all()

    # Combine data dictionary
    report_data = {
        "generated_at": datetime.utcnow().strftime("%B %d, %Y - %H:%M UTC"),
        "users": {
            "total": total_users,
            "active": active_users,
            "blocked": blocked_users,
            "verified": verified_users,
            "regular": regular_users,
            "owners": owner_users,
            "admins": admin_users
        },
        "owners": {
            "total": total_owners,
            "approved": approved_owners,
            "pending": pending_owners
        },
        "rooms": {
            "total": total_rooms,
            "approved": approved_rooms,
            "pending": pending_rooms,
            "available": available_rooms,
            "occupied": occupied_rooms,
            "avg_price": round(avg_price, 2),
            "max_price": round(max_price, 2),
            "min_price": round(min_price, 2),
            "total_inventory": round(total_inventory_value, 2)
        },
        "interests": {
            "total": total_interests,
            "pending": pending_interests,
            "accepted": accepted_interests,
            "rejected": rejected_interests
        },
        "financials": {
            "accepted_revenue": round(total_accepted_revenue, 2),
            "admin_commission": round(estimated_admin_earnings, 2)
        },
        "recent_rooms": recent_rooms
    }

    return render_template("admin_report.html", report=report_data)