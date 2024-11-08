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

@routes.route('/api/territories')
@login_required
def get_territories():
    try:
        return jsonify(VALID_TERRITORIES)
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@routes.route('/api/customers')
@login_required
def get_customers():
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

@routes.route('/customers', methods=['POST'])
@login_required
def create_customer():
    try:
        data = request.json
        
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
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/customers', methods=['PUT'])
@login_required
def update_customer():
    try:
        data = request.json
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
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/customers', methods=['DELETE'])
@login_required
def delete_customer():
    try:
        data = request.json
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
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/orders', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.json
        delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
        
        order = Order(
            customer_id=data['customer_id'],
            order_date=delivery_date,
            delivery_date=delivery_date,
            total_cases=0,
            total_cost=0,
            payment_cash=0,
            payment_check=0,
            payment_credit=0,
            payment_received=0,
            driver_expense=0
        )
        
        db.session.add(order)
        db.session.commit()

        customer = Customer.query.get(data['customer_id'])
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'customer_id': order.customer_id,
                'customer_name': customer.name,
                'order_date': order.order_date.isoformat(),
                'delivery_date': order.delivery_date.isoformat(),
                'total_cases': order.total_cases,
                'total_cost': float(order.total_cost),
                'payment_cash': float(order.payment_cash),
                'payment_check': float(order.payment_check),
                'payment_credit': float(order.payment_credit),
                'payment_received': float(order.payment_received),
                'isEditable': True
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/api/orders/<date>')
@login_required
def get_orders_by_date(date):
    try:
        delivery_date = datetime.strptime(date, '%Y-%m-%d').date()
        weekday = delivery_date.strftime('%A')
        
        orders = Order.query.join(Customer).filter(
            Order.delivery_date == delivery_date
        ).all()
        
        if delivery_date == datetime.now().date() and not orders:
            scheduled_customers = Customer.query.filter_by(delivery_day=weekday).all()
            
            for customer in scheduled_customers:
                order = Order(
                    customer_id=customer.id,
                    order_date=delivery_date,
                    delivery_date=delivery_date,
                    total_cases=0,
                    total_cost=0,
                    payment_cash=0,
                    payment_check=0,
                    payment_credit=0,
                    payment_received=0,
                    driver_expense=0
                )
                db.session.add(order)
            db.session.commit()
            
            orders = Order.query.join(Customer).filter(
                Order.delivery_date == delivery_date
            ).all()
        
        return jsonify([{
            'id': order.id,
            'customer_id': order.customer_id,
            'customer_name': order.customer.name,
            'order_date': order.order_date.isoformat(),
            'delivery_date': order.delivery_date.isoformat(),
            'total_cases': order.total_cases,
            'total_cost': float(order.total_cost),
            'payment_cash': float(order.payment_cash),
            'payment_check': float(order.payment_check),
            'payment_credit': float(order.payment_credit),
            'payment_received': float(order.payment_received),
            'isEditable': order.delivery_date == datetime.now().date()
        } for order in orders])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@routes.route('/api/orders/<int:order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    try:
        data = request.json
        order = Order.query.get_or_404(order_id)
        
        if 'total_cases' in data:
            order.total_cases = data['total_cases']
        if 'total_cost' in data:
            order.total_cost = Decimal(str(data['total_cost']))
            
        if 'payment_cash' in data:
            order.payment_cash = Decimal(str(data['payment_cash']))
        if 'payment_check' in data:
            order.payment_check = Decimal(str(data['payment_check']))
        if 'payment_credit' in data:
            order.payment_credit = Decimal(str(data['payment_credit']))
            
        order.payment_received = order.payment_cash + order.payment_check + order.payment_credit
        
        customer = order.customer
        old_balance = float(customer.balance)
        new_balance = old_balance + (float(order.total_cost) - float(order.payment_received))
        customer.balance = new_balance
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/invoice/<int:order_id>')
@login_required
def get_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    customer = order.customer
    
    filename = f"invoice_{customer.name}_{order.delivery_date}.pdf"
    filepath = os.path.join('/tmp', filename)
    
    generate_invoice_pdf(order, customer, filepath)
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@routes.route('/api/reports')
@login_required
def get_report_data():
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        territory = request.args.get('territory')
        
        # Base query
        query = Order.query.join(Customer)
        
        # Apply filters
        filters = [
            Order.delivery_date.between(start_date, end_date)
        ]
        if territory:
            filters.append(Customer.territory == territory)
            
        query = query.filter(and_(*filters))
        
        # Get orders
        orders = query.order_by(Order.delivery_date).all()
        
        # Calculate summary
        summary = {
            'total_orders': len(orders),
            'total_cases': sum(o.total_cases for o in orders),
            'total_revenue': float(sum(o.total_cost for o in orders)),
            'total_payments': float(sum(o.payment_received for o in orders)),
            'outstanding_balance': float(sum(o.total_cost - o.payment_received for o in orders))
        }
        
        # Format order data
        order_data = [{
            'delivery_date': o.delivery_date.isoformat(),
            'total_cases': o.total_cases,
            'total_cost': float(o.total_cost),
            'payment_cash': float(o.payment_cash),
            'payment_check': float(o.payment_check),
            'payment_credit': float(o.payment_credit),
            'payment_received': float(o.payment_received),
            'outstanding': float(o.total_cost - o.payment_received)
        } for o in orders]
        
        return jsonify({
            'summary': summary,
            'orders': order_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@routes.route('/download_report')
@login_required
def download_report():
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        territory = request.args.get('territory')
        
        # Base query
        query = Order.query.join(Customer)
        
        # Apply filters
        filters = [
            Order.delivery_date.between(start_date, end_date)
        ]
        if territory:
            filters.append(Customer.territory == territory)
            
        query = query.filter(and_(*filters))
        
        # Get orders
        orders = query.order_by(Order.delivery_date).all()
        
        # Calculate summary
        summary = {
            'total_orders': len(orders),
            'total_cases': sum(o.total_cases for o in orders),
            'total_revenue': float(sum(o.total_cost for o in orders)),
            'total_payments': float(sum(o.payment_received for o in orders)),
            'outstanding_balance': float(sum(o.total_cost - o.payment_received for o in orders))
        }
        
        # Format order data
        order_data = [{
            'order_date': o.delivery_date.isoformat(),
            'total_cases': o.total_cases,
            'total_cost': float(o.total_cost),
            'payment_cash': float(o.payment_cash),
            'payment_check': float(o.payment_check),
            'payment_credit': float(o.payment_credit),
            'payment_received': float(o.payment_received)
        } for o in orders]
        
        filename = f"report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join('/tmp', filename)
        
        generate_report_pdf(order_data, summary, start_date, end_date, territory, filepath)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400
