from flask import Blueprint, render_template, request, jsonify, flash, send_file, redirect, url_for
from flask_login import login_required
from models import Customer, Order, db
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, text
import os
import re
import logging

logger = logging.getLogger(__name__)
routes = Blueprint('routes', __name__)

VALID_TERRITORIES = ['North', 'South']

@routes.route('/api/health')
def health_check():
    """Health check endpoint to verify database connectivity"""
    try:
        logger.info("Performing health check")
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

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
            scheduled_customers = Customer.query.filter_by(delivery_day=weekday, is_active=True).all()
            
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
            'payment_received': float(order.payment_received or 0),
            'isEditable': delivery_date == datetime.now().date()
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
        customers = Customer.query.filter_by(is_active=True).all()
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
        if not data:
            raise ValueError("No data provided")
            
        order = Order.query.get_or_404(order_id)
        
        # Only allow updates to current day orders
        if order.delivery_date != datetime.now().date():
            logger.warning(f"Attempted to update past order: {order_id}")
            return jsonify({'error': 'Cannot modify past orders'}), 403
        
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
        return jsonify({'error': str(e)}), 400
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
        if not data:
            raise ValueError("No data provided")
            
        delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
        
        # Only allow creating orders for current day
        if delivery_date != datetime.now().date():
            logger.warning("Attempted to create order for non-current date")
            return jsonify({'error': 'Can only create orders for current date'}), 403
        
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
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error creating order: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error creating order: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/api/daily_driver_expense/<date>', methods=['GET'])
@login_required
def get_daily_driver_expense(date):
    try:
        logger.info(f"Loading driver expense for date: {date}")
        delivery_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get all orders for the date and sum their driver expenses
        total_expense = db.session.query(func.sum(Order.driver_expense))\
            .filter(Order.delivery_date == delivery_date)\
            .scalar() or 0
            
        logger.info(f"Retrieved driver expense for {date}: ${float(total_expense):.2f}")
        return jsonify({'amount': float(total_expense)})
    except ValueError as e:
        logger.error(f"Invalid date format in driver expense request: {str(e)}")
        return jsonify({'error': 'Invalid date format'}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving driver expense: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving driver expense: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/api/daily_driver_expense', methods=['POST'])
@login_required
def save_daily_driver_expense():
    try:
        data = request.json
        if not data or 'date' not in data or 'amount' not in data:
            raise ValueError("Missing required fields: date and amount")
            
        logger.info(f"Saving driver expense for date: {data['date']}")
        delivery_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        amount = Decimal(str(data['amount']))
        
        # Update driver expense for all orders on this date
        orders = Order.query.filter(Order.delivery_date == delivery_date).all()
        if not orders:
            logger.warning(f"No orders found for date {data['date']}")
            return jsonify({'error': 'No orders found for this date'}), 404
            
        # Distribute the amount evenly across all orders
        per_order_expense = amount / len(orders)
        for order in orders:
            order.driver_expense = per_order_expense
        
        db.session.commit()
        logger.info(f"Updated driver expense for {len(orders)} orders on {data['date']}")
        return jsonify({'success': True})
            
    except ValueError as e:
        logger.error(f"Invalid data format in driver expense update: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error updating driver expense: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error updating driver expense: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/invoice/<int:order_id>')
@login_required
def generate_invoice(order_id):
    try:
        logger.info(f"Generating invoice for order {order_id}")
        order = Order.query.get_or_404(order_id)
        customer = order.customer
        
        filename = f"invoice_{customer.name}_{order.delivery_date.strftime('%Y-%m-%d')}.pdf"
        filepath = os.path.join("/tmp", filename)
        
        from utils.pdf_generator import generate_invoice_pdf
        generate_invoice_pdf(order, customer, filepath)
        
        logger.info(f"Generated invoice: {filename}")
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except FileNotFoundError as e:
        logger.error(f"PDF file not found: {str(e)}")
        flash('Error generating invoice: PDF file not found', 'error')
        return redirect(url_for('routes.orders'))
    except Exception as e:
        logger.error(f"Error generating invoice: {str(e)}")
        flash('Error generating invoice', 'error')
        return redirect(url_for('routes.orders'))

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
            try:
                db.session.commit()
                logger.info(f"Added {len(customers)} test customers successfully")
            except SQLAlchemyError as e:
                logger.error(f"Database error adding test customers: {str(e)}")
                db.session.rollback()
                raise
        
        # Create some test orders for today
        today = datetime.now().date()
        if Order.query.filter(Order.delivery_date == today).count() == 0:
            logger.info(f"No orders found for {today}. Adding test orders...")
            for customer in Customer.query.filter_by(is_active=True).all():
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
            try:
                db.session.commit()
                logger.info("Test orders created successfully")
            except SQLAlchemyError as e:
                logger.error(f"Database error creating test orders: {str(e)}")
                db.session.rollback()
                raise
            
    except SQLAlchemyError as e:
        logger.error(f"Database error during test data creation: {str(e)}")
        db.session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during test data creation: {str(e)}")
        db.session.rollback()
        raise
