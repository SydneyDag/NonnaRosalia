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
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

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
            'total_cases': sum(day.total_cases for day in daily_totals),
            'total_revenue': float(sum(day.total_cost for day in daily_totals)),
            'total_payments': float(sum(day.total_payments for day in daily_totals)),
            'outstanding_balance': float(sum(day.total_cost - day.total_payments for day in daily_totals))
        }

        # Format daily totals
        daily_data = [{
            'delivery_date': day.delivery_date.isoformat(),
            'total_cases': day.total_cases,
            'total_cost': float(day.total_cost),
            'payment_cash': float(day.total_cash),
            'payment_check': float(day.total_check),
            'payment_credit': float(day.total_credit),
            'payment_received': float(day.total_payments),
            'outstanding': float(day.total_cost - day.total_payments)
        } for day in daily_totals]

        return jsonify({
            'orders': daily_data,
            'summary': summary
        })
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            'total_cases': sum(day.total_cases for day in daily_totals),
            'total_revenue': float(sum(day.total_cost for day in daily_totals)),
            'total_payments': float(sum(day.total_payments for day in daily_totals)),
            'outstanding_balance': float(sum(day.total_cost - day.total_payments for day in daily_totals))
        }

        # Format data for PDF
        daily_data = [{
            'order_date': day.delivery_date.isoformat(),
            'total_cases': day.total_cases,
            'total_cost': float(day.total_cost),
            'payment_cash': float(day.total_cash),
            'payment_check': float(day.total_check),
            'payment_credit': float(day.total_credit),
            'payment_received': float(day.total_payments)
        } for day in daily_totals]

        # Generate filename
        filename = f"report_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
        if territory:
            filename += f"_{territory}"
        filename += ".pdf"
        filepath = os.path.join("/tmp", filename)

        # Generate PDF
        generate_report_pdf(daily_data, summary, start_date, end_date, territory, filepath)

        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('routes.reports'))
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('routes.reports'))

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
        return jsonify({'success': True, 'id': order.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/invoice/<int:order_id>')
@login_required
def generate_invoice(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        customer = Customer.query.get_or_404(order.customer_id)
        
        # Clean customer name for filename
        clean_name = re.sub(r'[^\w\s-]', '', customer.name.lower())
        clean_name = re.sub(r'[\s]+', '_', clean_name)
        
        # Generate filename with customer name and delivery date
        filename = f"invoice_{clean_name}_{order.delivery_date.strftime('%Y-%m-%d')}.pdf"
        filepath = os.path.join("/tmp", filename)
        
        # Generate PDF
        generate_invoice_pdf(order, customer, filepath)
        
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error generating invoice: {str(e)}', 'error')
        return redirect(url_for('routes.orders'))

@routes.route('/customers', methods=['POST'])
@login_required
def create_customer():
    try:
        data = request.json
        if data['territory'] not in VALID_TERRITORIES:
            return jsonify({'error': 'Invalid territory. Must be either North or South'}), 400
            
        customer = Customer(
            name=data['name'],
            address=data['address'],
            delivery_day=data['delivery_day'],
            account_type=data['account_type'],
            territory=data['territory'],
            balance=0
        )
        db.session.add(customer)
        db.session.commit()
        return jsonify({'success': True, 'id': customer.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/customers', methods=['PUT'])
@login_required
def update_customer():
    try:
        data = request.json
        if data['territory'] not in VALID_TERRITORIES:
            return jsonify({'error': 'Invalid territory. Must be either North or South'}), 400
            
        customer = Customer.query.get_or_404(data['id'])
        customer.name = data['name']
        customer.address = data['address']
        customer.delivery_day = data['delivery_day']
        customer.account_type = data['account_type']
        customer.territory = data['territory']
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/customers', methods=['DELETE'])
@login_required
def delete_customer():
    try:
        data = request.json
        customer = Customer.query.get_or_404(data['id'])
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/api/daily_driver_expense/<date>', methods=['GET'])
@login_required
def get_daily_driver_expense(date):
    try:
        delivery_date = datetime.strptime(date, '%Y-%m-%d').date()
        orders = Order.query.filter(
            Order.delivery_date == delivery_date
        ).all()
        
        total_expense = sum(float(order.driver_expense or 0) for order in orders)
        return jsonify({'amount': total_expense})
    except ValueError:
        logger.error(f"Invalid date format received: {date}")
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        logger.error(f"Error retrieving daily driver expense: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@routes.route('/api/daily_driver_expense', methods=['POST'])
@login_required
def update_daily_driver_expense():
    try:
        data = request.json
        if not data or 'date' not in data or 'amount' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        delivery_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        amount = Decimal(str(data['amount']))

        # Update driver expense for all orders on this date
        orders = Order.query.filter(
            Order.delivery_date == delivery_date
        ).all()
        
        if orders:
            # Distribute the amount evenly among orders
            expense_per_order = amount / len(orders)
            for order in orders:
                order.driver_expense = expense_per_order
            
            db.session.commit()
            logger.info(f"Updated driver expense for {len(orders)} orders on {delivery_date}")
            return jsonify({'success': True})
        else:
            logger.warning(f"No orders found for date: {delivery_date}")
            return jsonify({'error': 'No orders found for the specified date'}), 404

    except ValueError as e:
        logger.error(f"Invalid data format: {str(e)}")
        return jsonify({'error': 'Invalid data format'}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500