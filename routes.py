from flask import Blueprint, render_template, request, jsonify, flash, send_file, redirect, url_for
from flask_login import login_required
from models import Customer, Order, db
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_
import os
import re
from utils.pdf_generator import generate_invoice_pdf, generate_report_pdf

routes = Blueprint('routes', __name__)

VALID_TERRITORIES = ['North', 'South']
VALID_DELIVERY_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
VALID_ACCOUNT_TYPES = ['Regular', 'Corporate']

def validate_customer_data(data, check_required=True):
    errors = []
    
    # Check required fields
    if check_required:
        required_fields = ['name', 'address', 'delivery_day', 'account_type', 'territory']
        for field in required_fields:
            if not data.get(field):
                errors.append(f'{field} is required')
    
    # Validate territory if provided
    if data.get('territory') and data['territory'] not in VALID_TERRITORIES:
        errors.append(f'Territory must be one of: {", ".join(VALID_TERRITORIES)}')
    
    # Validate delivery day if provided
    if data.get('delivery_day') and data['delivery_day'] not in VALID_DELIVERY_DAYS:
        errors.append(f'Delivery day must be one of: {", ".join(VALID_DELIVERY_DAYS)}')
    
    # Validate account type if provided
    if data.get('account_type') and data['account_type'] not in VALID_ACCOUNT_TYPES:
        errors.append(f'Account type must be one of: {", ".join(VALID_ACCOUNT_TYPES)}')
    
    return errors

@routes.route('/customers', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def manage_customers():
    if request.method == 'GET':
        try:
            customers = Customer.query.all()
            return jsonify([{
                'id': c.id,
                'name': c.name,
                'address': c.address,
                'delivery_day': c.delivery_day,
                'account_type': c.account_type,
                'territory': c.territory,
                'balance': float(c.balance)
            } for c in customers])
        except SQLAlchemyError as e:
            return jsonify({'error': str(e)}), 500
    
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    try:
        data = request.json
        
        if request.method == 'POST':
            # Validate input data
            errors = validate_customer_data(data)
            if errors:
                return jsonify({'error': '; '.join(errors)}), 400
            
            customer = Customer(
                name=data['name'],
                address=data['address'],
                delivery_day=data['delivery_day'],
                account_type=data['account_type'],
                territory=data['territory']
            )
            db.session.add(customer)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'customer': {
                    'id': customer.id,
                    'name': customer.name,
                    'address': customer.address,
                    'delivery_day': customer.delivery_day,
                    'account_type': customer.account_type,
                    'territory': customer.territory,
                    'balance': float(customer.balance)
                }
            }), 201
        
        elif request.method == 'PUT':
            if not data.get('id'):
                return jsonify({'error': 'Customer ID is required'}), 400
                
            # Validate input data
            errors = validate_customer_data(data, check_required=False)
            if errors:
                return jsonify({'error': '; '.join(errors)}), 400
                
            customer = Customer.query.get(data['id'])
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404
                
            # Update only provided fields
            if 'name' in data:
                customer.name = data['name']
            if 'address' in data:
                customer.address = data['address']
            if 'delivery_day' in data:
                customer.delivery_day = data['delivery_day']
            if 'account_type' in data:
                customer.account_type = data['account_type']
            if 'territory' in data:
                customer.territory = data['territory']
                
            db.session.commit()
            
            return jsonify({
                'success': True,
                'customer': {
                    'id': customer.id,
                    'name': customer.name,
                    'address': customer.address,
                    'delivery_day': customer.delivery_day,
                    'account_type': customer.account_type,
                    'territory': customer.territory,
                    'balance': float(customer.balance)
                }
            }), 200
        
        elif request.method == 'DELETE':
            if not data.get('id'):
                return jsonify({'error': 'Customer ID is required'}), 400
                
            customer = Customer.query.get(data['id'])
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404
                
            # Check if customer has any orders
            if customer.orders:
                return jsonify({'error': 'Cannot delete customer with existing orders'}), 400
                
            db.session.delete(customer)
            db.session.commit()
            
            return jsonify({'success': True}), 200
            
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@routes.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@routes.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@routes.route('/customers')
@login_required
def customers():
    return render_template('customers.html')

@routes.route('/orders')
@login_required
def orders():
    return render_template('orders.html')

# Note: The rest of the existing routes.py code would follow here