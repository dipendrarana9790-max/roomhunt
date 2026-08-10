from extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fullname = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(255))
    role = db.Column(db.Enum('user', 'owner', 'admin'), default='user')
    isadmin = db.Column(db.Boolean, default=False)
    isverified = db.Column(db.Boolean, default=False)
    isactive = db.Column(db.Boolean, default=True)

    # Relationships
    owner_profile = db.relationship('Owner', backref='user', uselist=False, foreign_keys='Owner.user_id')
    interests = db.relationship('Interested', backref='user', cascade="all, delete-orphan")

class Owner(db.Model):
    __tablename__ = 'owners'
    
    owner_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # --- Identity & KYC Verification ---
    citizenship_no = db.Column(db.String(50))
    citizenship_photo = db.Column(db.String(255))
    citizenship_back_photo = db.Column(db.String(255))
    profile_photo = db.Column(db.String(255))
    
    # --- Contact & Address ---
    address = db.Column(db.String(255))
    contact = db.Column(db.String(20))  # 👈 Make sure this line exists!
    
    # --- Approval & Verification Tracking ---
    approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rooms = db.relationship('Room', backref='owner', cascade="all, delete-orphan")

class Room(db.Model):
    __tablename__ = 'rooms'
    
    room_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.owner_id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    room_image = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    interests = db.relationship('Interested', backref='room', cascade="all, delete-orphan")


class Interested(db.Model):
    __tablename__ = 'interesteds'
    
    interest_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.room_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'accepted', 'rejected'), default='pending')
    interested_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint composite index to prevent duplicate entries for the same room by the same user
    __table_args__ = (
        db.UniqueConstraint('room_id', 'user_id', name='unique_room_user_interest'),
    )