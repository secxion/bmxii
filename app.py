import os
import hashlib
from flask import Flask, render_template, request, redirect, url_for, flash, session, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv  
from admin import VALID_ADMIN_KEYS

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Database (PostgreSQL for Railway, SQLite for local dev)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///contact.db')

# Convert PostgreSQL URL if needed (Railway uses old format)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-default-secret')

# Security settings
app.config['SESSION_COOKIE_SECURE'] = True  
app.config['SESSION_COOKIE_HTTPONLY'] = True  
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Add Flask-Migrate

# Contact Model
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

# Ensure database tables exist
with app.app_context():
    db.create_all()
    print("✅ Database setup complete!")

# Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/contact")
def contact():
    get_flashed_messages()
    return render_template("contact.html")

@app.route("/submit_contact", methods=["POST"])
def submit_contact():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        message = request.form["message"]

        if not name or not phone or not email or not message:
            flash("All fields are required!", "error")
            return redirect(url_for("contact"))

        new_message = Contact(name=name, phone=phone, email=email, message=message)
        db.session.add(new_message)
        db.session.commit()

        flash("Message sent successfully!", "success")
        return redirect(url_for("contact"))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        entered_key = request.form.get("admin_key")
        hashed_key = hashlib.sha256(entered_key.encode()).hexdigest()

        if hashed_key in VALID_ADMIN_KEYS:
            session["admin_authenticated"] = True
            flash("Login successful!", "success")
            return redirect(url_for("admin_messages"))

        flash("Invalid key! Access denied.", "error")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")

@app.route("/admin/messages")
def admin_messages():
    if not session.get("admin_authenticated"):
        flash("Unauthorized access! Please enter the admin key.", "error")
        return redirect(url_for("admin_login"))

    messages = Contact.query.all()
    return render_template("admin_messages.html", messages=messages)

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("admin_login"))

# Run the application
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
