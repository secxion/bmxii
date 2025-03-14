import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv  
from admin import VALID_ADMIN_KEYS  # Import admin keys

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contact.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define Contact model
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

# Create database tables
with app.app_context():
    db.create_all()
    print("Database setup complete!")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/contact")
def contact():
    get_flashed_messages()  # Clear previous flash messages
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

# 🔹 Admin Login Page (Enter Key)
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        entered_key = request.form.get("admin_key")

        if entered_key in VALID_ADMIN_KEYS:
            session["admin_authenticated"] = True
            return redirect(url_for("admin_messages"))  # Redirect to messages

        flash("Invalid key! Access denied.", "error")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")

# 🔹 Admin Panel (Requires Authentication)
@app.route("/admin/messages")
def admin_messages():
    if not session.get("admin_authenticated"):
        flash("Unauthorized access! Please enter the admin key.", "error")
        return redirect(url_for("admin_login"))

    messages = Contact.query.all()  # Fetch all messages
    return render_template("admin_messages.html", messages=messages)

# 🔹 Logout Route (Redirects to Admin Login)
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_authenticated", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("admin_login"))  # Redirect to admin login to prevent message showing in contact page

if __name__ == "__main__":
    app.run(debug=True)
