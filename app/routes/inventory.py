from flask import Blueprint, request, jsonify
from app import db
from app.models import Product, Category, ProductUnit, PurchaseOrderItem, ReturnableContainer
from datetime import datetime
from sqlalchemy import desc, or_
from app.utils.auth import token_required
from app.utils.gl_utils import get_latest_purchase_price

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


@token_required
@inventory_bp.route('/products', methods=['POST'])
def add_product():
    data = request.json

    # --- Validate product name & SKU ---
    if not data.get('name') or not data.get('sku'):
        return jsonify({"error": "Product name and SKU are required"}), 400

    # --- Create the product ---
    product = Product(
        name=data['name'],
        sku=data['sku'],
        category_id=data.get('category_id'),
        quantity=0,  # Always start at zero
        price=0,     # price is determined by units
        whole_price=0,
        status=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(product)
    db.session.flush()  # to get product.id before commit

    # --- Create related product units ---
    units_data = data.get('units', [])
    for unit_data in units_data:
        unit = ProductUnit(
            product_id=product.id,
            unit_name=unit_data.get('unit_name'),
            conversion_quantity=unit_data.get('conversion_quantity', 1),
            retail_price=unit_data.get('retail_price', 0.0),
            wholesale_price=unit_data.get('wholesale_price', 0.0),
            cost_price=unit_data.get('cost_price', 0.0),
            is_returnable=unit_data.get('is_returnable', False),
            status=1,
            # unit_code=unit_data.get('unit_code')
        )
        db.session.add(unit)
        db.session.flush()  # get unit.id

        # --- Automatically create ReturnableContainer if unit is returnable ---
        if unit.is_returnable and unit.conversion_quantity>1:
            container = ReturnableContainer(
                name=f"{unit.unit_name} Container",
                description=f"Container for {unit.unit_name} of {product.name}",
                unit_value=unit_data.get('cost_price', 0.0),
                total_in_stock=0,
                product_unit_id=unit.id,
                status=1,
            )
            db.session.add(container)

    db.session.commit()

    return jsonify({
        "message": "Product, units, and returnable containers saved successfully",
        "product_id": product.id
    }), 201


@token_required
@inventory_bp.route('/products', methods=['GET'])
def list_products():
    products = Product.query.filter(Product.status != 9).all()  # exclude deleted products
    # Fetch all non-deleted products, sorted by category name and then product name
    products = (
        Product.query
        .filter(Product.status != 9)  # exclude deleted
        .join(Category, Product.category_id == Category.id)
        .order_by(Category.name.asc(), Product.name.asc())
        .all()
    )
    result = []

    for p in products:
        category = db.session.query(Category).filter_by(id=p.category_id, status=1).first()
        # Get last purchase price for this unit
        # last_purchase = (
        #     PurchaseOrderItem.query
        #     .filter(PurchaseOrderItem.product_id==p.id, PurchaseOrderItem.status==1)
        #     .order_by(desc(PurchaseOrderItem.created_at))
        #     .first()
        # )
        last_purchase_price=get_latest_purchase_price(p.id)
        print(" last_purchase_price ",last_purchase_price)

        # last_purchase_price = last_purchase.unit_price if last_purchase else 0


        result.append({
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "category_id": p.category_id,
            "category_name": category.name if category else None,
            "quantity": p.quantity,
            "status": p.status,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "last_purchase_price"   : last_purchase_price,
            "units": [
                {
                    "id": u.id,
                    "unit_name": u.unit_name,
                    "conversion_quantity": u.conversion_quantity,
                    "retail_price": u.retail_price,
                    "wholesale_price": u.wholesale_price,
                    "cost_price": u.cost_price,
                    "is_returnable": u.is_returnable,
                    "unit_code": u.unit_code,
                    "containers": [
                        {
                            "id": c.id,
                            "name": c.name,
                            "description": c.description,
                            "unit_value": c.unit_value,
                            "total_issued": c.total_issued,
                            "total_returned": c.total_returned,
                            "total_damaged": c.total_damaged,
                            "total_in_stock": c.total_in_stock
                        }
                        for c in u.containers
                    ]
                }
                for u in p.units if u.status != 9  # ✅ include only active units

            ]
        })

    return jsonify(result)


@token_required
@inventory_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    category = Category.query.filter_by(id=product.category_id, status=1).first()

    last_purchase_price=get_latest_purchase_price(product.id)



    return jsonify({
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "category_id": product.category_id,
        "category_name": category.name if category else None,
        "quantity": product.quantity,
        "status": product.status,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "last_purchase_price"   : last_purchase_price,
        "units": [
            {
                "id": u.id,
                "unit_name": u.unit_name,
                "conversion_quantity": u.conversion_quantity,
                "retail_price": u.retail_price,
                "wholesale_price": u.wholesale_price,
                "cost_price": u.cost_price,
                "is_returnable": u.is_returnable,
                "unit_code": u.unit_code,
                "containers": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "description": c.description,
                        "unit_value": c.unit_value,
                        "total_issued": c.total_issued,
                        "total_returned": c.total_returned,
                        "total_damaged": c.total_damaged,
                        "total_in_stock": c.total_in_stock
                    }
                    for c in u.containers
                ]
            } for u in product.units if u.status != 9 
        ]
    })


@token_required
@inventory_bp.route('/products/search', methods=['GET'])
def search_product():
    name = request.args.get('name')
    query = Product.query.filter(Product.status != 9)  # ignore deleted products

    if name:
        # ✅ Case-insensitive search by name or SKU
        search_pattern = f"%{name}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.sku.ilike(search_pattern)
            )
        )

    products = query.all()
    result = []

    for p in products:
        category = db.session.query(Category).filter_by(id=p.category_id, status=1).first()
        # print("prints ",p.id)

        last_purchase_price=get_latest_purchase_price(p.id)
        print(" last_purchase_price ",last_purchase_price)

        result.append({
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "category_id": p.category_id,
            "category_name": category.name if category else None,
            "quantity": p.quantity,
            "status": p.status,
            "created_at": p.created_at,
            "last_purchase_price"   : last_purchase_price,
            "updated_at": p.updated_at,

            # ✅ Include all product units
            "units": [
                {
                    "id": u.id,
                    "unit_name": u.unit_name,
                    "conversion_quantity": u.conversion_quantity,
                    "retail_price": u.retail_price,
                    "wholesale_price": u.wholesale_price,
                    "is_returnable": u.is_returnable,
                    "unit_code": u.unit_code
                } for u in p.units if u.status != 9  
            ]
        })

    return jsonify(result)


@token_required
@inventory_bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json

    # --- Update main product fields ---
    product.name = data.get('name', product.name)
    product.sku = data.get('sku', product.sku)
    product.category_id = data.get('category_id', product.category_id)
    product.updated_at = datetime.utcnow()

    # --- Update product units if provided ---
    if 'units' in data:
        existing_units = ProductUnit.query.filter_by(product_id=product.id).all()

        # Soft-delete old units instead of hard deleting
        for unit in existing_units:
            unit.status = 9  # mark as deleted
            # Soft-delete associated containers
            containers = ReturnableContainer.query.filter_by(product_unit_id=unit.id).all()
            for container in containers:
                container.status = 9

        # Add or update units from request
        for unit_data in data['units']:
            # Check if unit exists by ID (if client sends unit ID)
            unit = None
            if 'id' in unit_data:
                unit = ProductUnit.query.filter_by(id=unit_data['id'], product_id=product.id).first()
            if unit:
                # Update existing unit
                unit.unit_name = unit_data.get('unit_name', unit.unit_name)
                unit.conversion_quantity = unit_data.get('conversion_quantity', unit.conversion_quantity)
                unit.retail_price = unit_data.get('retail_price', unit.retail_price)
                unit.wholesale_price = unit_data.get('wholesale_price', unit.wholesale_price)
                unit.cost_price = unit_data.get('cost_price', unit.cost_price)
                unit.is_returnable = unit_data.get('is_returnable', unit.is_returnable)
                unit.status = 1  # reactivate if previously soft-deleted
            else:
                # Add new unit
                unit = ProductUnit(
                    product_id=product.id,
                    unit_name=unit_data.get('unit_name'),
                    conversion_quantity=unit_data.get('conversion_quantity', 1),
                    retail_price=unit_data.get('retail_price', 0.0),
                    wholesale_price=unit_data.get('wholesale_price', 0.0),
                    cost_price=unit_data.get('cost_price', 0.0),
                    is_returnable=unit_data.get('is_returnable', False),
                    status=1,
                )
                db.session.add(unit)
                db.session.flush()

            # --- Handle returnable containers ---
            if unit.is_returnable and unit.conversion_quantity > 1:
                container = ReturnableContainer.query.filter_by(product_unit_id=unit.id).first()
                if container:
                    container.name = f"{unit.unit_name} Container"
                    container.description = f"Container for {unit.unit_name} of {product.name}"
                    container.unit_value = unit.cost_price
                    container.status = 1  # reactivate if previously soft-deleted
                else:
                    container = ReturnableContainer(
                        name=f"{unit.unit_name} Container",
                        description=f"Container for {unit.unit_name} of {product.name}",
                        unit_value=unit.cost_price,
                        total_in_stock=0,
                        product_unit_id=unit.id,
                        status=1,
                    )
                    db.session.add(container)

    db.session.commit()

    return jsonify({
        "message": "Product, units, and returnable containers updated successfully (soft-deleted old units with status=9)",
        "product_id": product.id
    })


# --- Delete product ---
@token_required
@inventory_bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    product.status = 9  # soft delete
    db.session.commit()
    return jsonify({"message": "Product deleted", "product_id": id})


# ---------------- Category CRUD ---------------- #

# --- Add category ---
@token_required
@inventory_bp.route('/categories', methods=['POST'])
def add_category():
    data = request.json
    category = Category(
        name=data['name'],
        description=data.get('description'),
        status=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({"message": "Category added", "category_id": category.id}), 201

# --- View all categories ---
@token_required
@inventory_bp.route('/categories', methods=['GET'])
def list_categories():
    categories = Category.query.all()
    result = [{"id": c.id, "name": c.name, "description": c.description,
               "status": c.status, "created_at": c.created_at, "updated_at": c.updated_at} 
              for c in categories]
    return jsonify(result)

# --- Find category by ID ---
@token_required
@inventory_bp.route('/categories/<int:id>', methods=['GET'])
def get_category(id):
    c = Category.query.get_or_404(id)
    return jsonify({
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "status": c.status,
        "created_at": c.created_at,
        "updated_at": c.updated_at
    })

# --- Update category ---
@token_required
@inventory_bp.route('/categories/<int:id>', methods=['PUT'])
def update_category(id):
    c = Category.query.get_or_404(id)
    data = request.json
    c.name = data.get('name', c.name)
    c.description = data.get('description', c.description)
    c.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Category updated", "category_id": c.id})

# --- Delete category ---
@token_required
@inventory_bp.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    c = Category.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Category deleted", "category_id": id})

@token_required
@inventory_bp.route('/products/<int:product_id>/units', methods=['GET'])
def get_product_units(product_id):
    product = Product.query.get_or_404(product_id)

    units = ProductUnit.query.filter_by(product_id=product.id).all()
    if not units:
        return jsonify({"message": "No units found for this product", "units": []}), 200

    result = [
        {
            "id": u.id,
            "unit_name": u.unit_name,
            "conversion_quantity": u.conversion_quantity,
            "retail_price": u.retail_price,
            "wholesale_price": u.wholesale_price,
            "cost_price": u.cost_price,
            "is_returnable": u.is_returnable,
            "unit_code": u.unit_code,
            "containers": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "unit_value": c.unit_value,
                    "total_issued": c.total_issued,
                    "total_returned": c.total_returned,
                    "total_damaged": c.total_damaged,
                    "total_in_stock": c.total_in_stock
                } for c in u.containers
            ]
        }
        for u in units if u.status != 9  
    ]

    return jsonify(result), 200
