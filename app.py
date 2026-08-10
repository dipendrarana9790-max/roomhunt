# app.py
from flask import Flask, render_template
from extensions import db  # Changed from mysql to db

app = Flask(__name__)

app.secret_key = "roomhunt_secret_key"

# 1. Update your database configuration to a URI format
# Format: mysql+pymysql://username:password@host/database_name
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/roomhunt"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["UPLOAD_FOLDER"] = "static/uploads"

# 2. Initialize SQLAlchemy with your app
db.init_app(app)

# Blueprints
from routes.auth import auth
from routes.admin import admin
from routes.owner import owner
from routes.user import user
from routes.public import public

app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(owner)
app.register_blueprint(user)
app.register_blueprint(public)

# @app.route("/")
# def home():
#     return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)