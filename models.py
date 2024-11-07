from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    delivery_day = db.Column(db.String(10), nullable=False)  # Monday, Tuesday, etc.
    account_type = db.Column(db.String(20), nullable=False)  # Regular, Premium, etc.
    territory = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0)
    orders = db.relationship('Order', backref='customer', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    delivery_date = db.Column(db.Date, nullable=False)
    total_cases = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Numeric(10, 2), nullable=False)
    
    # New payment tracking fields
    payment_cash = db.Column(db.Numeric(10, 2), default=0)
    payment_check = db.Column(db.Numeric(10, 2), default=0)
    payment_credit = db.Column(db.Numeric(10, 2), default=0)
    payment_received = db.Column(db.Numeric(10, 2), default=0)
    
    # New driver expense field
    driver_expense = db.Column(db.Numeric(10, 2), default=0)
    
    # New one-time delivery flag
    is_one_time_delivery = db.Column(db.Boolean, default=False)
    
    status = db.Column(db.String(20), default='pending')  # pending, delivered, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def total_payment(self):
        return float(self.payment_cash) + float(self.payment_check) + float(self.payment_credit)
