from flask import Blueprint, render_template, request, redirect, url_for, session
from extensions import db
from models import User

auth = Blueprint("auth", __name__)

# Signup
@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        confirm_password =request.form["confirm_password"]

        if password != confirm_password:
            return "password and confirm password should be same"

        # Check if email is already taken using filter_by
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already exists"

        # Create a new instance of the User model
        new_user = User(
            fullname=fullname,
            email=email,
            phone=phone,
            password=password,
            role="user",
            isadmin=False,
            isverified=False,
            isactive=True
        )

        # Add to session and commit to MySQL
        db.session.add(new_user)
        db.session.commit()

        # Safely assign session data using object properties
        session["user_id"] = new_user.id
        session["fullname"] = new_user.fullname
        session["email"] = new_user.email
        session["role"] = new_user.role

        return redirect("/")

    return render_template("signup.html")


# Login
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Query the user matching both email and password
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session["user_id"] = user.id
            session["fullname"] = user.fullname
            session["email"] = user.email
            session["role"] = user.role

            return redirect("/")

        return "Invalid Email or Password"

    return render_template("login.html")


# Logout
@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")  # ✅ Direct URL redirect without url_for()