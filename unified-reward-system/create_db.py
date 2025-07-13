from app import create_app, db
from app.models import Merchant

app = create_app()

with app.app_context():
    try:
        # ✅ Step 1: Create database tables if they don't exist
        db.create_all()  # ❗ This ensures the `merchant` table exists before inserting data

        # ✅ Step 2: Define merchant data
        merchants_data = [
            ("Dominos", 0.01, "http://localhost:5001/api/dominos/rewards"),
            ("Starbucks", 0.015, "http://localhost:5001/api/starbucks/rewards"),
            ("Amazon", 0.02, "http://localhost:5001/api/amazon/rewards"),
            ("Flipkart", 0.018, "http://localhost:5001/api/flipkart/rewards"),
        ]

        # ✅ Step 3: Insert merchants using `create_with_liquidity`
        merchants = []
        for name, redemption_value, api_url in merchants_data:
            merchant = Merchant.create_with_liquidity(name, redemption_value, api_url)
            merchants.append(merchant)

        print("✅ Merchants & Liquidity Pools Created Successfully!")

        # ✅ Debugging: Print inserted merchants and liquidity pools
        for merchant in merchants:
            print(f"Merchant: {merchant.name}, ID: {merchant.id}")
            print(f"Liquidity Pool for Merchant ID {merchant.id}, Balance: {merchant.liquidity_pool.balance}")

    except Exception as e:
        db.session.rollback()  # ❌ Rollback in case of any error
        print(f"❌ Error occurred: {e}")
