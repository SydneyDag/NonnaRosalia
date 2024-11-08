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

@routes.route('/api/customers')
@login_required
def get_customers():
    try:
        logger.info("Loading all customers")
        customers = Customer.query.order_by(Customer.name).all()
        
        customers_data = [{
            'id': customer.id,
            'name': customer.name,
            'address': customer.address,
            'delivery_day': customer.delivery_day,
            'account_type': customer.account_type,
            'territory': customer.territory,
            'balance': float(customer.balance or 0)
        } for customer in customers]
        
        logger.info(f"Successfully retrieved {len(customers_data)} customers")
        return jsonify(customers_data)
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving customers: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving customers: {str(e)}")
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
        
        orders = Order.query.join(Customer).filter(
            Order.delivery_date == delivery_date
        ).all()
        
        orders_data = [{
            'id': order.id,
            'customer_id': order.customer_id,
            'customer_name': order.customer.name,
            'total_cases': order.total_cases or 0,
            'total_cost': float(order.total_cost or 0),
            'payment_cash': float(order.payment_cash or 0),
            'payment_check': float(order.payment_check or 0),
            'payment_credit': float(order.payment_credit or 0),
            'payment_received': float(order.payment_received or 0),
            'isEditable': delivery_date == datetime.now().date()
        } for order in orders]
        
        logger.info(f"Retrieved {len(orders_data)} orders for {date}")
        return jsonify(orders_data)
    except ValueError as e:
        logger.error(f"Invalid date format: {str(e)}")
        return jsonify({'error': 'Invalid date format'}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving orders by date: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving orders by date: {str(e)}")
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

@routes.route('/api/daily_driver_expense/<date>', methods=['GET'])
@login_required
def get_daily_driver_expense(date):
    try:
        logger.info(f"Loading driver expense for date: {date}")
        delivery_date = datetime.strptime(date, '%Y-%m-%d').date()
        
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
        
        orders = Order.query.filter(Order.delivery_date == delivery_date).all()
        if not orders:
            logger.warning(f"No orders found for date {data['date']}")
            return jsonify({'error': 'No orders found for this date'}), 404
            
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

@routes.route('/api/reports')
@login_required
def get_report_data():
    try:
        # Add default dates if not provided
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if not start_date or not end_date:
            today = datetime.now().date()
            start_date = today.replace(day=1).isoformat()
            end_date = today.isoformat()
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        territory = request.args.get('territory')
        logger.info(f"Generating report from {start_date} to {end_date}, territory: {territory or 'All'}")

        # Base query with error handling
        query = db.session.query(
            Order.delivery_date,
            func.coalesce(func.sum(Order.total_cases), 0).label('total_cases'),
            func.coalesce(func.sum(Order.total_cost), 0).label('total_cost'),
            func.coalesce(func.sum(Order.payment_cash), 0).label('payment_cash'),
            func.coalesce(func.sum(Order.payment_check), 0).label('payment_check'),
            func.coalesce(func.sum(Order.payment_credit), 0).label('payment_credit'),
            func.coalesce(func.sum(Order.payment_received), 0).label('payment_received')
        ).join(Customer)

        query = query.filter(Order.delivery_date.between(start_date, end_date))
        if territory:
            query = query.filter(Customer.territory == territory)

        query = query.group_by(Order.delivery_date)
        daily_totals = query.all()

        if not daily_totals:
            logger.info("No data found for the specified criteria")
            return jsonify({
                'orders': [],
                'summary': {
                    'total_orders': 0,
                    'total_cases': 0,
                    'total_revenue': 0,
                    'total_payments': 0,
                    'outstanding_balance': 0
                }
            })

        # Format response with proper error handling
        orders_data = []
        for day in daily_totals:
            try:
                orders_data.append({
                    'delivery_date': day.delivery_date.isoformat(),
                    'total_cases': int(day.total_cases or 0),
                    'total_cost': float(day.total_cost or 0),
                    'payment_cash': float(day.payment_cash or 0),
                    'payment_check': float(day.payment_check or 0),
                    'payment_credit': float(day.payment_credit or 0),
                    'payment_received': float(day.payment_received or 0),
                    'outstanding': float(day.total_cost or 0) - float(day.payment_received or 0)
                })
            except (TypeError, ValueError) as e:
                logger.error(f"Error processing day {day.delivery_date}: {str(e)}")
                continue

        summary = {
            'total_orders': len(daily_totals),
            'total_cases': sum(int(day.total_cases or 0) for day in daily_totals),
            'total_revenue': sum(float(day.total_cost or 0) for day in daily_totals),
            'total_payments': sum(float(day.payment_received or 0) for day in daily_totals),
            'outstanding_balance': sum(float(day.total_cost or 0) - float(day.payment_received or 0) for day in daily_totals)
        }

        logger.info(f"Report generated successfully: {summary['total_orders']} orders, ${summary['total_revenue']:.2f} revenue")
        return jsonify({
            'orders': orders_data,
            'summary': summary
        })

    except ValueError as e:
        logger.error(f"Invalid date format in report request: {str(e)}")
        return jsonify({'error': 'Invalid date format'}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error generating report: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error generating report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500