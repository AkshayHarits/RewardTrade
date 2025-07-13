from app import db
from app.models import UserPoints, LiquidityPool, SmartExchange, Merchant
import requests
import logging
from flask import flash, redirect, url_for
from flask_login import current_user
from app.bpv_updater import get_merchant_bpv  # ✅ Fetch BPV dynamically
from app.tasks import process_smart_exchanges  # ✅ Ensure Celery task is correctly imported

# ✅ Initialize Logging
logging.basicConfig(level=logging.INFO)

def update_merchant_api(from_merchant, to_merchant, amount):
    """Sends updated user points to merchants after an exchange."""
    merchants_to_update = [from_merchant, to_merchant]

    for merchant in merchants_to_update:
        user_points = UserPoints.query.filter_by(user_id=current_user.id, merchant_id=merchant.id).first()
        points_change = -amount if merchant == from_merchant else amount

        payload = {
            "user_phone": current_user.phone,
            "points_change": points_change
        }

        merchant_url = f"{merchant.api_url}/rewards/update"
        print(f"🚀 Sending API Update to {merchant.name}: {merchant_url} with {payload}")

        try:
            response = requests.post(merchant_url, json=payload, timeout=10)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            response_data = response.json()

            if response_data.get('success'):
                print(f"✅ API Update for {merchant.name}: {response.status_code}, {response_data}")
            else:
                print(f"⚠️ API Update for {merchant.name} failed: {response_data}")

        except requests.RequestException as e:
            print(f"❌ Failed to update {merchant.name}: {str(e)}")
        except ValueError as e:
            print(f"❌ Invalid JSON response from {merchant.name}: {str(e)}")

def process_instant_exchange(from_merchant, to_merchant, amount, converted_amount):
    logging.info(f"🔹 Instant Exchange: {amount} points {from_merchant.name} → {to_merchant.name}")

    try:
        # Add validation for converted amount
        if converted_amount > amount * 2:
            return {"error": "Invalid conversion rate detected."}, 400

        with db.session.begin_nested():
            from_pool = LiquidityPool.query.filter_by(merchant_id=from_merchant.id).with_for_update().first()
            to_pool = LiquidityPool.query.filter_by(merchant_id=to_merchant.id).with_for_update().first()

            if not from_pool or not to_pool or from_pool.balance < amount:
                return {"error": "Insufficient liquidity. Please try Smart Exchange."}, 400

            user_points_from = UserPoints.query.filter_by(user_id=current_user.id, merchant_id=from_merchant.id).with_for_update().first()
            user_points_to = UserPoints.query.filter_by(user_id=current_user.id, merchant_id=to_merchant.id).with_for_update().first()

            if not user_points_from or user_points_from.points < amount:
                return {"error": "Insufficient points for exchange."}, 400

            if not user_points_to:
                user_points_to = UserPoints(user_id=current_user.id, merchant_id=to_merchant.id, points=0)
                db.session.add(user_points_to)

            # Add maximum points validation
            if user_points_to.points + converted_amount > 1000000:  # Prevent unreasonable accumulation
                return {"error": "Maximum points limit reached for target merchant."}, 400

            user_points_from.points -= amount
            user_points_to.points += converted_amount
            from_pool.balance -= amount
            to_pool.balance += converted_amount

        db.session.commit()
        
        # Update merchant APIs
        update_merchant_api(from_merchant, current_user.phone, -amount)
        update_merchant_api(to_merchant, current_user.phone, converted_amount)

        return {"success": True, "message": f"Converted {amount} points from {from_merchant.name} to {converted_amount} {to_merchant.name} points."}, 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"❌ Instant Exchange Failed: {e}")
        return {"error": "Transaction failed. Please try again."}, 500


def process_smart_exchange(from_merchant, to_merchant, amount):
    """Handles Smart Exchange request and triggers Celery."""
    logging.info(f"🔹 Smart Exchange: {amount} points {from_merchant.name} → {to_merchant.name}")
    try:
        with db.session.begin():  # Use transaction
            # Fetch BPV for both merchants
            from_bpv = get_merchant_bpv(from_merchant)
            to_bpv = get_merchant_bpv(to_merchant)

            # Validate conversion rate
            if to_bpv <= 0:
                flash("Invalid conversion rate. Please try again later.", "error")
                return redirect(url_for("main.dashboard"))

            # Calculate exchange rate using BPV (Fair conversion)
            conversion_rate = from_bpv / to_bpv
            converted_amount = int(amount * conversion_rate)

            # Validate user points
            user_points_from = UserPoints.query.filter_by(user_id=current_user.id, merchant_id=from_merchant.id).first()
            if not user_points_from or user_points_from.points < amount:
                flash("Insufficient points for exchange.", "error")
                return redirect(url_for("main.dashboard"))

            # Store Smart Exchange request in DB
            new_order = SmartExchange(
                user_id=current_user.id,
                from_merchant_id=from_merchant.id,
                to_merchant_id=to_merchant.id,
                amount=amount,
                status="pending"
            )
            db.session.add(new_order)
            db.session.commit()

            flash(f"Smart Exchange request for {amount} points submitted. Processing...", "info")

            # Trigger Celery task to process cyclic matching
            process_smart_exchanges.delay()

    except Exception as e:
        db.session.rollback()
        logging.error(f"❌ Smart Exchange Failed: {e}")
        flash("Transaction failed, please try again.", "error")
        return redirect(url_for("main.dashboard"))