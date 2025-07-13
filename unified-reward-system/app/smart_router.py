from app.models import LiquidityPool

def smart_route(from_merchant, to_merchant, amount):
    """Determines if a transaction should use Smart Exchange or Instant Exchange."""
    from_pool = LiquidityPool.query.filter_by(merchant_id=from_merchant.id).first()
    to_pool = LiquidityPool.query.filter_by(merchant_id=to_merchant.id).first()
    
    liquidity_threshold = 5000  # Max allowed instant exchange

    if amount > liquidity_threshold or from_pool.balance < (amount * 1.1) or to_pool.balance < (amount * 1.1):
        print("🔄 Smart Exchange Enforced (Large transaction detected)")
        return 'smart'
    
    return 'instant'
