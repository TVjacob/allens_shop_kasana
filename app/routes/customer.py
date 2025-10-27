from flask import Blueprint, request, jsonify
from app import db
from app.models import Customer
from datetime import datetime

from app.utils.auth import token_required

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

# ------------------ Customers CRUD ------------------

# --- Add a new customer ---
@customer_bp.route('/', methods=['POST'])
@token_required

def add_customer():
    data = request.json
    customer = Customer(
        name=data.get('name', 'Walk-in'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        status=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify({"message": "Customer added", "customer_id": customer.id}), 201

# --- List all customers ---
@customer_bp.route('/', methods=['GET'])
@token_required

def list_customers():
    customers = Customer.query.all()
    result = [
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "email": c.email,
            "address": c.address,
            "status": c.status,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        }
        for c in customers
    ]
    return jsonify(result)

# --- Get customer by ID ---
@token_required

@customer_bp.route('/<int:id>', methods=['GET'])
def get_customer(id):
    c = Customer.query.get_or_404(id)
    return jsonify({
        "id": c.id,
        "name": c.name,
        "phone": c.phone,
        "email": c.email,
        "address": c.address,
        "status": c.status,
        "created_at": c.created_at,
        "updated_at": c.updated_at
    })

# --- Search customers by name, phone, or email ---
@token_required

@customer_bp.route('/search', methods=['GET'])
def search_customer():
    query = Customer.query
    search = request.args.get('query')
    # phone = request.args.get('phone')
    # email = request.args.get('email')
    if search:
        query = query.filter(Customer.name.ilike(f"%{search}%"))
        query = query.filter(Customer.phone.ilike(f"%{search}%"))
        query = query.filter(Customer.email.ilike(f"%{search}%"))
    customers = query.all()
    result = [
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "email": c.email,
            "address": c.address,
            "status": c.status,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        }
        for c in customers
    ]
    return jsonify(result)

# --- Update customer ---
@token_required

@customer_bp.route('/<int:id>', methods=['PUT'])
def update_customer(id):
    c = Customer.query.get_or_404(id)
    data = request.json
    c.name = data.get('name', c.name)
    c.phone = data.get('phone', c.phone)
    c.email = data.get('email', c.email)
    c.address = data.get('address', c.address)
    c.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Customer updated", "customer_id": c.id})

# --- Delete customer ---
@token_required

@customer_bp.route('/<int:id>', methods=['DELETE'])
def delete_customer(id):
    c = Customer.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Customer deleted", "customer_id": id})
