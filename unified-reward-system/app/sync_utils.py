import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app import db
from app.models import UserPoints, Merchant

def sync_user_points(user, fetch_from_api=False):
    """Sync user points. Fetch from API only during registration, otherwise update API with DB values."""
    if not user or not user.phone:
        return

    # Configure retry strategy for API calls
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))

    if fetch_from_api:  # Only during registration
        merchants = Merchant.query.all()
        for merchant in merchants:
            try:
                response = session.get(f"{merchant.api_url}/rewards/{user.phone}", timeout=10)
                if response.status_code == 200:
                    points = response.json().get("points", 0)
                    user_points = UserPoints.query.filter_by(user_id=user.id, merchant_id=merchant.id).first()
                    if not user_points:
                        user_points = UserPoints(user_id=user.id, merchant_id=merchant.id, points=points)
                        db.session.add(user_points)
                    else:
                        user_points.points = points
                else:
                    print(f"⚠️ API fetch failed for {merchant.name}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error fetching points from {merchant.name}: {e}")
        db.session.commit()

    else:  # Update API after exchange
        merchants = Merchant.query.all()
        for merchant in merchants:
            user_points = UserPoints.query.filter_by(user_id=user.id, merchant_id=merchant.id).first()
            points = user_points.points if user_points else 0
            try:
                response = session.post(
                    f"{merchant.api_url}/rewards/update",
                    json={"user_phone": user.phone, "points_change": points},
                    timeout=10
                )
                if response.status_code != 200:
                    print(f"⚠️ Failed to update {merchant.name} API: {response.text}")
            except Exception as e:
                print(f"❌ Failed to update {merchant.name}: {e}")