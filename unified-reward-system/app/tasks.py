from app import db, celery  # ✅ Now Celery is initialized correctly
from app.models import SmartExchange
from app.cyclic_matcher import find_exchange_cycles, execute_cycle
import logging

@celery.task
def process_smart_exchanges():
    """Background task to process all pending Smart Exchanges using cyclic matching."""
    logging.info("🔄 Processing Smart Exchanges...")

    with db.session.begin():
        pending_exchanges = SmartExchange.query.filter_by(status='pending').with_for_update().all()
        
        if not pending_exchanges:
            logging.info("✅ No pending Smart Exchanges.")
            return

        # ✅ Find and process exchange cycles
        cycles = find_exchange_cycles(pending_exchanges)
        
        if cycles:
           logging.info(f"✅ Found {len(cycles)} exchange cycles. Executing...")
           for cycle in cycles:
              execute_cycle(cycle)
        else:   
    # ✅ Complete unmatched exchanges to prevent hanging
            for exchange in pending_exchanges:
                exchange.status = 'failed'
            logging.info("⚠ No cycles found. Marked pending exchanges as failed.")

        db.session.commit()
