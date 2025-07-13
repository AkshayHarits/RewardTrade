from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import requests
import logging

from app import db, login_manager
from app.models import User, UserPoints, Merchant, SmartExchange, LiquidityPool
from app.bpv_updater import get_merchant_bpv, update_merchant_bpv
from app.sync_utils import sync_user_points
from app.smart_router import smart_route
from app.exchange_utils import process_instant_exchange, process_smart_exchange , update_merchant_api # ✅ Moved exchange functions

# Initialize Logging
logging.basicConfig(level=logging.INFO)

main = Blueprint("main", __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # ✅ Ensures user is fetched from the database

@main.route("/")
def home():
    return render_template("home.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        phone = request.form.get("phone")

        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose a different one.", "error")
            return redirect(url_for("main.register"))

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, password=hashed_password, phone=phone)

        try:
            db.session.add(new_user)
            db.session.commit()

            # ✅ Fetch and store initial points only once
            sync_user_points(new_user)

            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("main.login"))

        except IntegrityError:
            db.session.rollback()
            flash("This phone number is already registered. Please use a different number or log in if this is your account.", "error")
            return redirect(url_for("main.register"))

    return render_template("register.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template("login.html")

@main.route("/logout")
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("main.home"))

@main.route("/dashboard")
@login_required  # ✅ Ensures only logged-in users can access
def dashboard():
    if not current_user or not current_user.is_authenticated:
        flash("You must be logged in to access the dashboard.", "error")
        return redirect(url_for("main.login"))  # ✅ Redirect to login if user is None

    # ✅ Debugging output
    print(f"✅ Debug: current_user = {current_user}")
    print(f"✅ Debug: Username = {getattr(current_user, 'username', 'No username')}")
    print(f"✅ Debug: Phone = {getattr(current_user, 'phone', 'No phone')}")

    if not hasattr(current_user, "phone") or not current_user.phone:
        flash("Error: User profile is incomplete. Please update your profile.", "error")
        return redirect(url_for("main.dashboard"))

    sync_user_points(current_user)  # 🚀 Now only runs if `phone` exists

    merchants = Merchant.query.all()
    user_points = current_user.points.all()

    return render_template("dashboard.html", user=current_user, user_points=user_points, merchants=merchants)

@main.route("/convert_points", methods=["POST"])
@login_required
def convert_points():
    try:
        from_merchant_name = request.json.get("from_merchant")
        to_merchant_name = request.json.get("to_merchant")
        amount_str = request.json.get("amount")
        exchange_type = request.json.get("exchange_type")

        if not from_merchant_name or not to_merchant_name or not amount_str:
            return jsonify({"error": "Invalid request. Missing merchant or amount."}), 400

        amount = int(amount_str)
        from_merchant = Merchant.query.filter_by(name=from_merchant_name).first()
        to_merchant = Merchant.query.filter_by(name=to_merchant_name).first()

        if not from_merchant or not to_merchant:
            return jsonify({"error": "Invalid merchants selected."}), 400

        # Add validation for amount
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400

        # Fix conversion rate calculation
        from_value = from_merchant.redemption_value
        to_value = to_merchant.redemption_value

        conversion_rate = min(2.0, max(0.1, (from_value / to_value) if to_value > 0 else 1))
        converted_amount = min(int(round(amount * conversion_rate)), amount * 2)
        
        if exchange_type == "instant":
            if amount > 1000:
                return jsonify({"error": "Amount must be less than 1000 points for instant exchange."}), 400
            response, status_code = process_instant_exchange(from_merchant, to_merchant, amount, converted_amount)
        else:
            response, status_code = process_smart_exchange(from_merchant, to_merchant, amount)

        if status_code == 200:
            sync_user_points(current_user, fetch_from_api=False)
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    
@main.route("/get_points")
@login_required
def get_points():
    """Fetches user points from merchant APIs and database fallback."""
    user_points = UserPoints.query.filter_by(user_id=current_user.id).all()
    merchant_ids = [up.merchant_id for up in user_points]
    merchants = {m.id: m for m in Merchant.query.filter(Merchant.id.in_(merchant_ids)).all()}

    points_data = {}
    for up in user_points:
        merchant = merchants.get(up.merchant_id)
        if not merchant:
            continue

        # Fetch live balance from API
        try:
            response = requests.get(f"{merchant.api_url}/{current_user.phone}")
            if response.status_code == 200:
                api_data = response.json()
                points_data[merchant.name] = api_data.get("points", 0)
            else:
                points_data[merchant.name] = up.points  # Fallback to DB value
        except requests.RequestException:
            points_data[merchant.name] = up.points  # Fallback in case of API failure

    return jsonify(points_data)
