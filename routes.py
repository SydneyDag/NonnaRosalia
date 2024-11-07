from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models import Customer, Order, db
from datetime import datetime
from decimal import Decimal

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

    if request.method == 'POST':
        data = request.json
        order = Order(
            customer_id=data['customer_id'],
            delivery_date=datetime.strptime(data['delivery_date'], '%Y-%m-%d'),
            total_cases=data['total_cases'],
            total_cost=data['total_cost'],
            payment_received=data.get('payment_received', 0)
        )
        customer = Customer.query.get(data['customer_id'])
        customer.balance = float(customer.balance) + (float(data['total_cost']) - float(data.get('payment_received', 0)))
        db.session.add(order)
        db.session.commit()
        return jsonify({'success': True, 'id': order.id})

@routes.route('/api/orders/<delivery_date>')
@login_required
def get_orders(delivery_date):
    date_obj = datetime.strptime(delivery_date, '%Y-%m-%d')
    orders = Order.query.filter_by(delivery_date=date_obj).all()
    return jsonify([{
        'id': o.id,
        'customer_name': o.customer.name,
        'total_cases': o.total_cases,
        'total_cost': float(o.total_cost),
        'payment_received': float(o.payment_received),
        'status': o.status
    } for o in orders])
