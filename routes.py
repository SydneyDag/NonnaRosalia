from flask import Blueprint, render_template, request, jsonify, flash, send_file
from flask_login import login_required
from models import Customer, Order, db
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_
import os
from utils.pdf_generator import generate_invoice_pdf, generate_report_pdf

routes = Blueprint('routes', __name__)

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

@routes.route('/api/orders/<date>')
@login_required
def get_orders_by_date(date):
    try:
        delivery_date = datetime.strptime(date, '%Y-%m-%d').date()
        orders = Order.query.join(Customer).filter(Order.delivery_date == delivery_date).all()
        
        # If it's today's date and no orders exist, create empty orders for scheduled customers
        if delivery_date == datetime.now().date() and not orders:
            # Get customers scheduled for today's weekday
            weekday = delivery_date.strftime('%A')
            scheduled_customers = Customer.query.filter_by(delivery_day=weekday).all()
            
            # Create empty orders for scheduled customers
            orders = []
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
            
            # Reload orders
            orders = Order.query.join(Customer).filter(Order.delivery_date == delivery_date).all()
        
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
            'payment_received': float(order.payment_received)
        } for order in orders])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@routes.route('/api/orders/<int:order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    try:
        data = request.json
        order = Order.query.get_or_404(order_id)
        
        # Update order details
        if 'total_cases' in data:
            order.total_cases = data['total_cases']
        if 'total_cost' in data:
            order.total_cost = Decimal(str(data['total_cost']))
            
        # Update payment information
        if 'payment_cash' in data:
            order.payment_cash = Decimal(str(data['payment_cash']))
        if 'payment_check' in data:
            order.payment_check = Decimal(str(data['payment_check']))
        if 'payment_credit' in data:
            order.payment_credit = Decimal(str(data['payment_credit']))
            
        # Calculate total payment
        order.payment_received = order.payment_cash + order.payment_check + order.payment_credit
        
        # Update customer balance
        customer = order.customer
        old_balance = float(customer.balance)
        new_balance = old_balance + (float(order.total_cost) - float(order.payment_received))
        customer.balance = new_balance
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/api/daily_driver_expense/<date>')
@login_required
def get_daily_driver_expense(date):
    try:
        delivery_date = datetime.strptime(date, '%Y-%m-%d').date()
        expense = Order.query.filter(
            Order.delivery_date == delivery_date,
            Order.driver_expense > 0
        ).with_entities(func.sum(Order.driver_expense)).scalar()
        
        return jsonify({'amount': float(expense) if expense else 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@routes.route('/api/daily_driver_expense', methods=['POST'])
@login_required
def save_daily_driver_expense():
    try:
        data = request.json
        delivery_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        amount = Decimal(str(data['amount']))
        
        orders = Order.query.filter_by(delivery_date=delivery_date).all()
        if orders:
            expense_per_order = amount / len(orders)
            for order in orders:
                order.driver_expense = expense_per_order
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'No orders found for this date'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Add test customers
def create_test_customers():
    if Customer.query.count() == 0:
        print("Creating test customers...")
        test_customers = [
            Customer(name="John's Store", address="123 Main St", delivery_day="Monday", 
                    account_type="Regular", territory="North"),
            Customer(name="Mary's Market", address="456 Oak Ave", delivery_day="Wednesday",
                    account_type="Premium", territory="South"),
            Customer(name="City Beverages", address="789 Pine Rd", delivery_day="Friday",
                    account_type="Regular", territory="North")
        ]
        for customer in test_customers:
            db.session.add(customer)
        try:
            db.session.commit()
            print("Test customers created successfully")
        except Exception as e:
            print(f"Error creating test customers: {e}")
            db.session.rollback()

# Create test customers when the app starts
create_test_customers()
