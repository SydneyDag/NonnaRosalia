import os
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError
import time

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

# Database configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key_123"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
    "connect_args": {
        "connect_timeout": 10
    }
}

MAX_RETRIES = 3
RETRY_DELAY = 2

def init_database():
    """Initialize database with retry logic"""
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            logger.info("Attempting database initialization...")
            db.init_app(app)
            with app.app_context():
                db.engine.connect()
                # Test query to verify connection
                db.session.execute('SELECT 1')
                db.session.commit()
            logger.info("Database connection successful")
            return True
        except OperationalError as e:
            retry_count += 1
            logger.error(f"Database connection failed (attempt {retry_count}/{MAX_RETRIES}): {str(e)}")
            if retry_count < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.critical("Failed to connect to database after maximum retries")
                raise
        except DatabaseError as e:
            logger.critical(f"Critical database error: {str(e)}")
            raise
        except Exception as e:
            logger.critical(f"Unexpected error during database initialization: {str(e)}")
            raise

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

# Global error handlers
@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 error: {str(error)}")
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    db.session.rollback()
    return jsonify({'error': 'Internal server error occurred'}), 500

@app.errorhandler(SQLAlchemyError)
def handle_db_error(error):
    logger.error(f"Database error: {str(error)}")
    db.session.rollback()
    return jsonify({'error': 'Database error occurred'}), 500

@app.errorhandler(Exception)
def handle_generic_error(error):
    logger.error(f"Unexpected error: {str(error)}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

# Initialize database
init_database()

# Register blueprints and initialize application
with app.app_context():
    import models
    from auth import auth, init_auth
    from routes import routes, create_test_data
    
    app.register_blueprint(auth)
    app.register_blueprint(routes)
    init_auth(app)
    
    try:
        logger.info("Starting application initialization...")
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully")
        
        logger.info("Initializing admin user...")
        create_admin_user()
        
        logger.info("Creating test data...")
        create_test_data()
        logger.info("Application initialization completed successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during application startup: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during application startup: {str(e)}")
        raise
