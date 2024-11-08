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

with app.app_context():
    import models
    from auth import auth, init_auth
    from routes import routes
    
    app.register_blueprint(auth)
    app.register_blueprint(routes)
    init_auth(app)
    
    try:
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully")
        create_admin_user()
    except Exception as e:
        print(f"Error during application startup: {str(e)}")
        raise
