from . import db
from datetime import datetime,timezone
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    points = db.relationship('UserPoints', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    smart_exchanges = db.relationship('SmartExchange', backref='user', lazy='dynamic', cascade='all, delete-orphan')

class Merchant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    redemption_value = db.Column(db.Float, nullable=False)  # 1 point = X dollars
    api_url = db.Column(db.String(200), nullable=False)
    supply = db.Column(db.Integer, default=1000)  # Adjusted dynamically
    demand = db.Column(db.Integer, default=1000)  # Adjusted dynamically
    msf = db.Column(db.Float, default=1.0)  # Market Sensitivity Factor
    sdbf = db.Column(db.Float, default=1.0)  # Supply-Demand Balancing Factor
    last_update = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # ✅ Corrected
    liquidity_pool = db.relationship('LiquidityPool', backref='merchant', uselist=False, cascade='all, delete-orphan')

    # Auto-create liquidity pool when a merchant is registered
    def __init__(self, name, redemption_value, api_url):
        self.name = name
        self.redemption_value = redemption_value
        self.api_url = api_url

    @staticmethod
    def create_with_liquidity(name, redemption_value, api_url, balance=5000):
        """Ensure Merchant is created before creating Liquidity Pool"""
        merchant = Merchant(name=name, redemption_value=redemption_value, api_url=api_url)
        db.session.add(merchant)
        db.session.commit()  # ✅ Commit merchant first to get ID
        
        return merchant

class UserPoints(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False)
    points = db.Column(db.Integer, default=0)
    __table_args__ = (db.UniqueConstraint('user_id', 'merchant_id', name='uix_user_merchant'),)

class LiquidityPool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False, unique=True)
    balance = db.Column(db.Integer, default=0)
    
class SmartExchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    from_merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False)
    to_merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # ✅ Corrected
    from_merchant = db.relationship('Merchant', foreign_keys=[from_merchant_id])
    to_merchant = db.relationship('Merchant', foreign_keys=[to_merchant_id])

from sqlalchemy.event import listens_for
from sqlalchemy.sql import text

@listens_for(Merchant, "after_insert")
def create_liquidity_pool(mapper, connection, target):
    """Automatically create a liquidity pool when a new merchant is added."""
    connection.execute(
        text("INSERT INTO liquidity_pool (merchant_id, balance) VALUES (:merchant_id, :balance)"),
        {"merchant_id": target.id, "balance": 5000}
    ) 