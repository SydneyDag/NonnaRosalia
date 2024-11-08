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
        return jsonify(VALID_TERRITORIES)
    except Exception as e:
        logger.error(f"Error getting territories: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/api/reports')
@login_required
def get_reports():
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        territory = request.args.get('territory', '')

        # Base query with date range and optional territory filter
        base_query = Order.query.join(Customer)
        if territory:
            base_query = base_query.filter(Customer.territory == territory)

        # Group by date and calculate daily totals
        daily_totals = (
            base_query.filter(Order.delivery_date.between(start_date, end_date))
            .with_entities(
                Order.delivery_date,
                func.sum(Order.total_cases).label('total_cases'),
                func.sum(Order.total_cost).label('total_cost'),
                func.sum(Order.payment_cash).label('total_cash'),
                func.sum(Order.payment_check).label('total_check'),
                func.sum(Order.payment_credit).label('total_credit'),
                func.sum(Order.payment_received).label('total_payments')
            )
            .group_by(Order.delivery_date)
            .order_by(Order.delivery_date)
            .all()
        )

        # Calculate overall summary
        summary = {
            'total_orders': len(daily_totals),
            'total_cases': sum(day.total_cases or 0 for day in daily_totals),
            'total_revenue': float(sum(day.total_cost or 0 for day in daily_totals)),
            'total_payments': float(sum(day.total_payments or 0 for day in daily_totals)),
            'outstanding_balance': float(sum((day.total_cost or 0) - (day.total_payments or 0) for day in daily_totals))
        }

        # Format daily totals
        daily_data = [{
            'delivery_date': day.delivery_date.isoformat(),
            'total_cases': day.total_cases or 0,
            'total_cost': float(day.total_cost or 0),
            'payment_cash': float(day.total_cash or 0),
            'payment_check': float(day.total_check or 0),
            'payment_credit': float(day.total_credit or 0),
            'payment_received': float(day.total_payments or 0),
            'outstanding': float((day.total_cost or 0) - (day.total_payments or 0))
        } for day in daily_totals]

        logger.info(f"Generated report for period {start_date} to {end_date}")
        return jsonify({
            'orders': daily_data,
            'summary': summary
        })
    except ValueError as e:
        logger.error(f"Invalid date format in report request: {str(e)}")
        return jsonify({'error': 'Invalid date format'}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error in report generation: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in report generation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/download_report')
@login_required
def download_report():
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        territory = request.args.get('territory', '')

        # Use the same query as /api/reports to maintain consistency
        base_query = Order.query.join(Customer)
        if territory:
            base_query = base_query.filter(Customer.territory == territory)

        daily_totals = (
            base_query.filter(Order.delivery_date.between(start_date, end_date))
            .with_entities(
                Order.delivery_date,
                func.sum(Order.total_cases).label('total_cases'),
                func.sum(Order.total_cost).label('total_cost'),
                func.sum(Order.payment_cash).label('total_cash'),
                func.sum(Order.payment_check).label('total_check'),
                func.sum(Order.payment_credit).label('total_credit'),
                func.sum(Order.payment_received).label('total_payments')
            )
            .group_by(Order.delivery_date)
            .order_by(Order.delivery_date)
            .all()
        )

        summary = {
            'total_orders': len(daily_totals),
            'total_cases': sum(day.total_cases or 0 for day in daily_totals),
            'total_revenue': float(sum(day.total_cost or 0 for day in daily_totals)),
            'total_payments': float(sum(day.total_payments or 0 for day in daily_totals)),
            'outstanding_balance': float(sum((day.total_cost or 0) - (day.total_payments or 0) for day in daily_totals))
        }

        # Format data for PDF
        daily_data = [{
            'order_date': day.delivery_date.isoformat(),
            'total_cases': day.total_cases or 0,
            'total_cost': float(day.total_cost or 0),
            'payment_cash': float(day.total_cash or 0),
            'payment_check': float(day.total_check or 0),
            'payment_credit': float(day.total_credit or 0),
            'payment_received': float(day.total_payments or 0)
        } for day in daily_totals]

        # Generate filename
        filename = f"report_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
        if territory:
            filename += f"_{territory}"
        filename += ".pdf"
        filepath = os.path.join("/tmp", filename)

        # Generate PDF
        generate_report_pdf(daily_data, summary, start_date, end_date, territory, filepath)

        logger.info(f"Generated PDF report: {filename}")
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except ValueError as e:
        logger.error(f"Invalid date format in PDF report request: {str(e)}")
        flash('Invalid date format', 'error')
        return redirect(url_for('routes.reports'))
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('routes.reports'))

@routes.route('/api/customers')
@login_required
def get_customers():
    try:
        customers = Customer.query.all()
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'address': c.address,
            'delivery_day': c.delivery_day,
            'account_type': c.account_type,
            'territory': c.territory,
            'balance': float(c.balance or 0)
        } for c in customers])
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving customers: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving customers: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/api/orders/<date>')
@login_required
def get_orders_by_date(date):
    try:
        delivery_date = datetime.strptime(date, '%Y-%m-%d').date()
        weekday = delivery_date.strftime('%A')
        
        orders = Order.query.join(Customer).filter(
            Order.delivery_date == delivery_date,
            Customer.delivery_day == weekday
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
                Order.delivery_date == delivery_date,
                Customer.delivery_day == weekday
            ).all()
        
        return jsonify([{
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
        } for order in orders])
    except ValueError as e:
        logger.error(f"Invalid date format in orders request: {str(e)}")
        return jsonify({'error': 'Invalid date format'}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving orders: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving orders: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

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
            
        order.payment_received = (order.payment_cash or 0) + (order.payment_check or 0) + (order.payment_credit or 0)
        
        customer = order.customer
        old_balance = float(customer.balance or 0)
        new_balance = old_balance + (float(order.total_cost or 0) - float(order.payment_received or 0))
        customer.balance = new_balance
        
        db.session.commit()
        logger.info(f"Updated order {order_id} successfully")
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
        logger.info(f"Created new order for customer {data['customer_id']}")
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
        
        # Add customers if none exist
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
