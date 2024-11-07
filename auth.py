from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required
from models import User, db
import logging

auth = Blueprint('auth', __name__)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt for username: {username}")
        
        if not username or not password:
            print("Login failed: Missing username or password")
            flash('Username and password are required')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"Login failed: User not found: {username}")
            flash('Invalid username or password')
            return render_template('login.html')
            
        if user.check_password(password):
            print(f"Login successful for user: {username}")
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        else:
            print(f"Login failed: Invalid password for user: {username}")
            flash('Invalid username or password')
            
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    print(f"User logged out: {request.user.username if hasattr(request, 'user') else 'Unknown'}")
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('auth.login'))

def init_auth(app):
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.init_app(app)
