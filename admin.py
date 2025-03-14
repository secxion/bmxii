from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from admin_keys import VALID_ADMIN_KEYS  # Import admin keys from separate file
from app import db, Contact  # Import database and Contact model

# Create a Blueprint for admin routes
admin_bp = Blueprint("admin", __name__)

# 🔹 Admin Login Page (Enter Key)
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        entered_key = request.form.get("admin_key")

        # Check if the entered key is valid
        if entered_key in VALID_ADMIN_KEYS:
            session["admin_authenticated"] = True
            flash("Login successful!", "success")
            return redirect(url_for("admin.admin_messages"))  # Redirect to messages

        flash("Invalid key! Access denied.", "error")
        return redirect(url_for("admin.admin_login"))

    return render_template("admin_login.html")

# 🔹 Admin Panel (Requires Authentication)
@admin_bp.route("/messages")
def admin_messages():
    if not session.get("admin_authenticated"):
        flash("Unauthorized access! Please enter the admin key.", "error")
        return redirect(url_for("admin.admin_login"))

    # Fetch all messages from the database
    messages = Contact.query.all()
    
    return render_template("admin_messages.html", messages=messages)

# 🔹 Admin Logout Route
@admin_bp.route("/logout")
def admin_logout():
    session.clear()  # Clear session instead of just popping "admin_authenticated"
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))
