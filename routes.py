from flask import Blueprint, render_template, request, jsonify, flash, send_file, redirect, url_for
from flask_login import login_required
from models import Customer, Order, db
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_
import os
import re
import logging
from utils.pdf_generator import generate_invoice_pdf, generate_report_pdf

logger = logging.getLogger(__name__)
routes = Blueprint('routes', __name__)

VALID_TERRITORIES = ['North', 'South']

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
        logger.info("Getting territories list")
        return jsonify(VALID_TERRITORIES)
    except Exception as e:
        logger.error(f"Error getting territories: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/api/orders')
@login_required
def get_all_orders():
    try:
        logger.info("Loading all orders")
        orders = Order.query.join(Customer).order_by(Order.delivery_date.desc()).all()
        
        orders_data = [{
            'id': order.id,
            'customer_id': order.customer_id,
            'customer_name': order.customer.name,
            'order_date': order.order_date.isoformat(),
            'delivery_date': order.delivery_date.isoformat(),
            'total_cases': order.total_cases or 0,
            'total_cost': float(order.total_cost or 0),
            'payment_cash': float(order.payment_cash or 0),
            'payment_check': float(order.payment_check or 0),
            'payment_credit': float(order.payment_credit or 0),
            'payment_received': float(order.payment_received or 0)
        } for order in orders]
        
        logger.info(f"Successfully retrieved {len(orders_data)} orders")
        return jsonify(orders_data)
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving all orders: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving all orders: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/api/orders/<date>')
@login_required
def get_orders_by_date(date):
    try:
        logger.info(f"Loading orders for date: {date}")
        delivery_date = datetime.strptime(date, '%Y-%m-%d').date()
        weekday = delivery_date.strftime('%A')
        
        orders = Order.query.join(Customer).filter(
            Order.delivery_date == delivery_date,
            Customer.delivery_day == weekday
        ).all()
        
        if delivery_date == datetime.now().date() and not orders:
            logger.info(f"No orders found for today ({date}). Creating empty orders for scheduled customers.")
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
            
            try:
                db.session.commit()
                logger.info(f"Created {len(scheduled_customers)} empty orders for {date}")
            except SQLAlchemyError as e:
                logger.error(f"Error creating empty orders: {str(e)}")
                db.session.rollback()
                raise
            
            orders = Order.query.join(Customer).filter(
                Order.delivery_date == delivery_date,
                Customer.delivery_day == weekday
            ).all()
        
        orders_data = [{
            'id': order.id,
            'customer_id': order.customer_id,
            'customer_name': order.customer.name,
            'order_date': order.order_date.isoformat(),
            'delivery_date': order.delivery_date.isoformat(),
            'total_cases': order.total_cases or 0,
            'total_cost': float(order.total_cost or 0),
            'payment_cash': float(order.payment_cash or 0),
            'payment_check': float(order.payment_check or 0),
            'payment_credit': float(order.payment_credit or 0),
            'payment_received': float(order.payment_received or 0)
        } for order in orders]
        
        logger.info(f"Successfully retrieved {len(orders_data)} orders for {date}")
        return jsonify(orders_data)
    except ValueError as e:
        logger.error(f"Invalid date format in orders request: {str(e)}")
        return jsonify({'error': 'Invalid date format'}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving orders: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving orders: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/api/customers')
@login_required
def get_customers():
    try:
        logger.info("Loading all customers")
        customers = Customer.query.all()
        customers_data = [{
            'id': c.id,
            'name': c.name,
            'address': c.address,
            'delivery_day': c.delivery_day,
            'account_type': c.account_type,
            'territory': c.territory,
            'balance': float(c.balance or 0)
        } for c in customers]
        
        logger.info(f"Successfully retrieved {len(customers_data)} customers")
        return jsonify(customers_data)
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving customers: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving customers: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/api/orders/<int:order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    try:
        logger.info(f"Updating order {order_id}")
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
            
        order.payment_received = (order.payment_cash or 0) + (order.payment_check or 0) + (order.payment_credit or 0)
        
        customer = order.customer
        old_balance = float(customer.balance or 0)
        new_balance = old_balance + (float(order.total_cost or 0) - float(order.payment_received or 0))
        customer.balance = new_balance
        
        db.session.commit()
        logger.info(f"Successfully updated order {order_id}")
        return jsonify({'success': True})
    except ValueError as e:
        logger.error(f"Invalid data format in order update: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Invalid data format'}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error updating order: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error updating order: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/orders', methods=['POST'])
@login_required
def create_order():
    try:
        logger.info("Creating new order")
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
        logger.info(f"Created new order {order.id} for customer {data['customer_id']}")
        return jsonify({'success': True, 'id': order.id})
    except ValueError as e:
        logger.error(f"Invalid data format in order creation: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Invalid data format'}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error creating order: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error creating order: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

def create_test_data():
    """Create initial test data for customers and orders."""
    try:
        logger.info("Creating test data...")
        
        # Create test customers
        customers = [
            Customer(name="North Store", address="123 North St", delivery_day="Monday", account_type="Regular", territory="North"),
            Customer(name="South Market", address="456 South Ave", delivery_day="Wednesday", account_type="Corporate", territory="South"),
            Customer(name="Downtown Shop", address="789 Main St", delivery_day="Friday", account_type="Regular", territory="North")
        ]
        
        if Customer.query.count() == 0:
            logger.info("No customers found. Adding test customers...")
            for customer in customers:
                db.session.add(customer)
            db.session.commit()
            logger.info(f"Added {len(customers)} test customers successfully")
        
        # Create some test orders for today
        today = datetime.now().date()
        if Order.query.filter(Order.delivery_date == today).count() == 0:
            logger.info(f"No orders found for {today}. Adding test orders...")
            for customer in Customer.query.all():
                order = Order(
                    customer_id=customer.id,
                    order_date=today,
                    delivery_date=today,
                    total_cases=10,
                    total_cost=100.00,
                    payment_cash=25.00,
                    payment_check=25.00,
                    payment_credit=25.00,
                    payment_received=75.00
                )
                db.session.add(order)
            db.session.commit()
            logger.info("Test orders created successfully")
            
    except SQLAlchemyError as e:
        logger.error(f"Database error during test data creation: {str(e)}")
        db.session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during test data creation: {str(e)}")
        db.session.rollback()
        raise
