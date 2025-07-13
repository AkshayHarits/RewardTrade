from app import create_app
from apscheduler.schedulers.background import BackgroundScheduler
from app.rebalance_liquidity import rebalance_liquidity
import atexit

# Create Flask App
app = create_app()

# Initialize and Start Scheduler AFTER Flask App is Created
scheduler = BackgroundScheduler()
scheduler.add_job(rebalance_liquidity, 'interval', hours=1)  # Runs every 1 hour
scheduler.start()

# Ensure Scheduler Stops When App Exits
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    app.run(debug=True)
