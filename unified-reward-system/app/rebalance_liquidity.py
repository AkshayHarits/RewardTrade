from app import db, create_app
from app.models import LiquidityPool, Merchant

def rebalance_liquidity():
    """Adjust liquidity pools based on supply-demand every 24 hours."""
    app = create_app()
    with app.app_context():
        merchants = Merchant.query.all()
        updates = []
        for merchant in merchants:
            pool = LiquidityPool.query.filter_by(merchant_id=merchant.id).first()
            if not pool:
                continue

            # Prevent division by zero
            if merchant.supply == 0 or merchant.demand == 0:
                continue

            # Calculate balance change based on supply-demand ratio
            ratio = merchant.demand / merchant.supply
            balance_change = int(min(100, abs(merchant.supply - merchant.demand) * 0.02))

            # Ensure balance remains within valid range
            new_balance = pool.balance + (balance_change if merchant.supply > merchant.demand else -balance_change)
            new_balance = max(0, min(1000000, new_balance))  # Ensure balance is between 0 and 1,000,000

            pool.balance = new_balance
            updates.append(pool)

        if updates:
            db.session.bulk_save_objects(updates)
            db.session.commit()
        print("✅ Liquidity Pools Rebalanced")