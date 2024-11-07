from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required
from models import Customer, Order, db
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError

routes = Blueprint('routes', __name__)

@routes.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

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
        orders = Order.query.filter_by(delivery_date=date_obj).all()
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
