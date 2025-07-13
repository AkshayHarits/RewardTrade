from app import db
from app.models import Merchant
from app.bpv_calculator import update_msf, update_sdbf, calculate_bpv
from datetime import datetime,timezone

def update_merchant_bpv():
    """Updates BPV (Business Point Value) for each merchant dynamically."""
    merchants = Merchant.query.all()
    for merchant in merchants:
        if merchant.last_update.tzinfo is None:  # ✅ Convert naive datetime to UTC
          merchant.last_update = merchant.last_update.replace(tzinfo=timezone.utc)

        time_since_update = (datetime.now(timezone.utc) - merchant.last_update).total_seconds() / 3600  # ✅ Fixed

        if time_since_update >= 24:
            merchant.msf = update_msf(merchant.msf, merchant.trade_volume, time_since_update)
            merchant.sdbf = update_sdbf(merchant.sdbf, merchant.supply, merchant.demand)
            merchant.trade_volume = 0
            merchant.last_update = datetime.now(timezone.utc)
            merchant.bpv = calculate_bpv(merchant.redemption_value, merchant.msf, merchant.sdbf)  # ✅ Store BPV in DB
    
    db.session.commit()  # ✅ Save all updates

def get_merchant_bpv(merchant):
    """Returns the Business Point Value (BPV) of a given merchant."""
    return calculate_bpv(merchant.redemption_value, merchant.msf, merchant.sdbf)