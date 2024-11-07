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

@routes.route('/customers', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def customers():
    if request.method == 'GET':
        return render_template('customers.html')
    
    try:
        if request.method == 'POST':
            data = request.json
            customer = Customer(
                name=data['name'],
                address=data['address'],
                delivery_day=data['delivery_day'],
                account_type=data['account_type'],
                territory=data['territory']
            )
            db.session.add(customer)
            db.session.commit()
            return jsonify({'success': True, 'id': customer.id})

        if request.method == 'PUT':
            data = request.json
            customer = Customer.query.get_or_404(data['id'])
            customer.name = data['name']
            customer.address = data['address']
            customer.delivery_day = data['delivery_day']
            customer.account_type = data['account_type']
            customer.territory = data['territory']
            db.session.commit()
            return jsonify({'success': True})

        if request.method == 'DELETE':
            customer_id = request.json['id']
            customer = Customer.query.get_or_404(customer_id)
            db.session.delete(customer)
            db.session.commit()
            return jsonify({'success': True})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/api/territories')
@login_required
def get_territories():
    territories = db.session.query(Customer.territory).distinct().all()
    return jsonify([t[0] for t in territories])

@routes.route('/api/reports')
@login_required
def get_reports():
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
        territory = request.args.get('territory')

        # Build the base query
        query = db.session.query(Order).join(Customer)
        
        # Apply filters
        query = query.filter(Order.order_date.between(start_date, end_date))
        if territory:
            query = query.filter(Customer.territory == territory)

        # Execute query
        orders = query.all()

        # Prepare orders data
        orders_data = [{
            'order_date': order.order_date.isoformat(),
            'territory': order.customer.territory,
            'customer_name': order.customer.name,
            'total_cases': order.total_cases,
            'total_cost': float(order.total_cost),
            'payment_received': float(order.payment_received),
            'status': order.status
        } for order in orders]

        # Calculate summary
        summary = {
            'total_orders': len(orders),
            'total_cases': sum(o.total_cases for o in orders),
            'total_revenue': float(sum(o.total_cost for o in orders)),
            'total_payments': float(sum(o.payment_received for o in orders)),
            'outstanding_balance': float(sum(o.total_cost - o.payment_received for o in orders))
        }

        return jsonify({
            'orders': orders_data,
            'summary': summary
        })

    except ValueError as e:
        return jsonify({'error': 'Invalid date format'}), 400
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 400

@routes.route('/api/customers')
@login_required
def get_customers():
    # Get filter parameters
    territory = request.args.get('territory')
    delivery_day = request.args.get('delivery_day')
    account_type = request.args.get('account_type')

    # Build query with filters
    query = Customer.query
    
    if territory:
        query = query.filter(Customer.territory == territory)
    if delivery_day:
        query = query.filter(Customer.delivery_day == delivery_day)
    if account_type:
        query = query.filter(Customer.account_type == account_type)

    customers = query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'address': c.address,
        'delivery_day': c.delivery_day,
        'account_type': c.account_type,
        'territory': c.territory,
        'balance': float(c.balance)
    } for c in customers])

@routes.route('/orders', methods=['GET', 'POST', 'PUT'])
@login_required
def orders():
    if request.method == 'GET':
        return render_template('orders.html')

    try:
        if request.method == 'POST':
            data = request.json
            
            # Validate payment amounts
            payment_cash = Decimal(str(data.get('payment_cash', 0)))
            payment_check = Decimal(str(data.get('payment_check', 0)))
            payment_credit = Decimal(str(data.get('payment_credit', 0)))
            total_payment = payment_cash + payment_check + payment_credit
            
            if total_payment > Decimal(str(data['total_cost'])):
                return jsonify({'error': 'Total payment cannot exceed total cost'}), 400
            
            order = Order(
                customer_id=data['customer_id'],
                delivery_date=datetime.strptime(data['delivery_date'], '%Y-%m-%d'),
                total_cases=data['total_cases'],
                total_cost=data['total_cost'],
                payment_cash=payment_cash,
                payment_check=payment_check,
                payment_credit=payment_credit,
                payment_received=total_payment,
                driver_expense=data.get('driver_expense', 0),
                is_one_time_delivery=data.get('is_one_time_delivery', False)
            )
            
            customer = Customer.query.get(data['customer_id'])
            customer.balance = float(customer.balance) + (float(data['total_cost']) - float(total_payment))
            
            db.session.add(order)
            db.session.commit()
            return jsonify({'success': True, 'id': order.id})

        if request.method == 'PUT':
            data = request.json
            order = Order.query.get_or_404(data['id'])
            
            if 'status' in data:
                order.status = data['status']
            else:
                # Update payment information
                payment_cash = Decimal(str(data.get('payment_cash', 0)))
                payment_check = Decimal(str(data.get('payment_check', 0)))
                payment_credit = Decimal(str(data.get('payment_credit', 0)))
                total_payment = payment_cash + payment_check + payment_credit
                
                if total_payment > Decimal(str(data['total_cost'])):
                    return jsonify({'error': 'Total payment cannot exceed total cost'}), 400
                
                order.payment_cash = payment_cash
                order.payment_check = payment_check
                order.payment_credit = payment_credit
                order.payment_received = total_payment
                order.driver_expense = data.get('driver_expense', order.driver_expense)
                order.is_one_time_delivery = data.get('is_one_time_delivery', order.is_one_time_delivery)
                
                # Update customer balance
                customer = order.customer
                old_payment = float(order.payment_received)
                new_payment = float(total_payment)
                customer.balance = float(customer.balance) - (new_payment - old_payment)
            
            db.session.commit()
            return jsonify({'success': True})
            
    except (SQLAlchemyError, ValueError) as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/api/orders/<delivery_date>')
@login_required
def get_orders(delivery_date):
    try:
        date_obj = datetime.strptime(delivery_date, '%Y-%m-%d')
        
        # Get additional filter parameters
        customer_id = request.args.get('customer_id')
        status = request.args.get('status')
        end_date = request.args.get('end_date')

        # Build query with filters
        query = Order.query

        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Order.delivery_date.between(date_obj, end_date_obj))
        else:
            query = query.filter_by(delivery_date=date_obj)

        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        if status:
            query = query.filter_by(status=status)

        orders = query.all()
        return jsonify([{
            'id': o.id,
            'customer_id': o.customer_id,
            'customer_name': o.customer.name,
            'total_cases': o.total_cases,
            'total_cost': float(o.total_cost),
            'payment_cash': float(o.payment_cash),
            'payment_check': float(o.payment_check),
            'payment_credit': float(o.payment_credit),
            'payment_received': float(o.payment_received),
            'driver_expense': float(o.driver_expense),
            'is_one_time_delivery': o.is_one_time_delivery,
            'status': o.status
        } for o in orders])
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

@routes.route('/api/daily_driver_expense/<date>', methods=['GET'])
@login_required
def get_daily_driver_expense(date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        orders = Order.query.filter_by(delivery_date=date_obj).all()
        total_expense = sum(float(order.driver_expense) for order in orders)
        return jsonify({'amount': total_expense})
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

@routes.route('/api/daily_driver_expense', methods=['POST'])
@login_required
def save_daily_driver_expense():
    try:
        data = request.json
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
        amount = Decimal(str(data['amount']))

        # Update all orders for the day with equal portions of the driver expense
        orders = Order.query.filter_by(delivery_date=date_obj).all()
        if orders:
            expense_per_order = amount / len(orders)
            for order in orders:
                order.driver_expense = expense_per_order
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'No orders found for this date'}), 404
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@routes.route('/download_invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        customer = order.customer
        
        # Create temporary file
        filename = f"invoice_{order_id}.pdf"
        filepath = os.path.join("/tmp", filename)
        
        generate_invoice_pdf(order, customer, filepath)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@routes.route('/download_report')
@login_required
def download_report():
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
        territory = request.args.get('territory')

        # Build the base query
        query = db.session.query(Order).join(Customer)
        
        # Apply filters
        query = query.filter(Order.order_date.between(start_date, end_date))
        if territory:
            query = query.filter(Customer.territory == territory)

        # Execute query
        orders = query.all()

        # Prepare orders data
        orders_data = [{
            'order_date': o.order_date.isoformat(),
            'customer_name': o.customer.name,
            'total_cases': o.total_cases,
            'total_cost': float(o.total_cost),
            'payment_received': float(o.payment_received),
            'status': o.status
        } for o in orders]

        # Calculate summary
        summary = {
            'total_orders': len(orders),
            'total_cases': sum(o.total_cases for o in orders),
            'total_revenue': float(sum(o.total_cost for o in orders)),
            'total_payments': float(sum(o.payment_received for o in orders)),
            'outstanding_balance': float(sum(o.total_cost - o.payment_received for o in orders))
        }

        # Generate PDF
        filename = f"report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join("/tmp", filename)
        
        generate_report_pdf(orders_data, summary, start_date, end_date, territory, filepath)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400
