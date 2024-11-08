import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        logger.info("Checking for existing admin user...")
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            logger.info(f"Admin user already exists (ID: {admin.id})")
            # Verify password hash exists
            if not admin.password_hash:
                logger.info("Updating admin password hash...")
                admin.set_password('admin123')
                db.session.commit()
                logger.info("Admin password hash updated successfully")
        else:
            logger.info("Creating new admin user...")
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            logger.info(f"Admin user created successfully (ID: {admin.id})")
            
        # Verify the password works
        if admin.check_password('admin123'):
            logger.info("Admin password verification successful")
        else:
            logger.warning("Admin password verification failed!")
            
    except SQLAlchemyError as e:
        logger.error(f"Database error during admin user creation: {str(e)}")
        db.session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during admin user creation: {str(e)}")
        db.session.rollback()
        raise

with app.app_context():
    import models
    from auth import auth, init_auth
    from routes import routes, create_test_data
    
    app.register_blueprint(auth)
    app.register_blueprint(routes)
    init_auth(app)
    
    try:
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully")
        create_admin_user()
        create_test_data()
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}")
        raise
