import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key_123"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

def create_admin_user():
    try:
        from models import User
        print("Checking for existing admin user...")
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print(f"Admin user already exists (ID: {admin.id})")
            # Verify password hash exists
            if not admin.password_hash:
                print("Updating admin password hash...")
                admin.set_password('admin123')
                db.session.commit()
                print("Admin password hash updated successfully")
        else:
            print("Creating new admin user...")
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created successfully (ID: {admin.id})")
            
        # Verify the password works
        if admin.check_password('admin123'):
            print("Admin password verification successful")
        else:
            print("WARNING: Admin password verification failed!")
            
    except SQLAlchemyError as e:
        print(f"Database error during admin user creation: {str(e)}")
        db.session.rollback()
        raise
    except Exception as e:
        print(f"Unexpected error during admin user creation: {str(e)}")
        db.session.rollback()
        raise

def create_test_customers():
    try:
        from models import Customer
        if Customer.query.count() == 0:
            print("Creating test customers...")
            test_customers = [
                Customer(
                    name="North Store 1",
                    address="123 Main St",
                    delivery_day="Monday",
                    account_type="Regular",
                    territory="North",
                    is_active=True
                ),
                Customer(
                    name="South Market",
                    address="456 Oak Ave",
                    delivery_day="Wednesday",
                    account_type="Corporate",
                    territory="South",
                    is_active=True
                ),
                Customer(
                    name="Weekend Shop",
                    address="789 Pine Rd",
                    delivery_day="Saturday",
                    account_type="Regular",
                    territory="North",
                    is_active=True
                ),
                Customer(
                    name="City Beverages",
                    address="321 Elm St",
                    delivery_day="Friday",
                    account_type="Corporate",
                    territory="South",
                    is_active=True
                ),
                Customer(
                    name="Inactive Store",
                    address="654 Maple Dr",
                    delivery_day="Monday",
                    account_type="Regular",
                    territory="North",
                    is_active=False
                )
            ]
            for customer in test_customers:
                db.session.add(customer)
            db.session.commit()
            print("Test customers created successfully")
    except Exception as e:
        print(f"Error creating test customers: {str(e)}")
        db.session.rollback()
        raise

with app.app_context():
    import models
    from auth import auth, init_auth
    from routes import routes
    
    app.register_blueprint(auth)
    app.register_blueprint(routes)
    init_auth(app)
    
    try:
        print("Creating database tables if they don't exist...")
        db.create_all()
        print("Database tables created/verified successfully")
        create_admin_user()
        create_test_customers()
    except Exception as e:
        print(f"Error during application startup: {str(e)}")
        raise
