from flask import Blueprint, request, jsonify
# Suppliers Blueprint for managing supplier and purchase order operations.
# This module provides CRUD operations for suppliers and purchase orders, including:
# - Retrieving all suppliers or a single supplier by ID.
# - Adding, updating, and deleting suppliers.
# - Retrieving all purchase orders or a specific purchase order by ID.
# - Adding new purchase orders with multiple items, updating existing purchase orders, and deleting them.
# - Handling payments for purchase orders.

# Purchase Order Status:
# 1 = Ready to Invoice
# 2 = Partially Paid
# 3 = Fully Paid
from app import db
from app.models import Account, Category, ContainerTransaction, InventoryTransaction, Product, ProductUnit, ReturnableContainer, Supplier, PurchaseOrder, PurchaseOrderItem, SupplierPayment
from app.utils.auth import token_required
from app.utils.gl_utils import post_to_ledger, generate_transaction_number
from datetime import datetime

from sqlalchemy.orm import joinedload
# from flask import jsonify

suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

# ------------------ Supplier CRUD ------------------ #

@token_required
# Get all suppliers
@suppliers_bp.route('/', methods=['GET'])
def get_suppliers():
    print("Request headers:", request.headers)

    suppliers = Supplier.query.filter_by(status=1).all()
    data = [{
        'id': s.id,
        'name': s.name,
        'contact': s.contact,
        'email': s.email,
        'status': s.status,
        'created_at': s.created_at
    } for s in suppliers]
    return jsonify(data), 200


@token_required
# Get single supplier
@suppliers_bp.route('/<int:id>', methods=['GET'])

def get_supplier(id):
    s = Supplier.query.get_or_404(id)
    return jsonify({
        'id': s.id,
        'name': s.name,
        'contact': s.contact,
        'email': s.email,
        'status': s.status,
        'created_at': s.created_at
    })


@token_required
# Add a new supplier
@suppliers_bp.route('/', methods=['POST'])

def add_supplier():
    data = request.get_json()
    supplier = Supplier(
        name=data['name'],
        contact=data.get('contact'),
        email=data.get('email'),
        status=1
    )
    db.session.add(supplier)
    db.session.commit()
    return jsonify({'message': 'Supplier created successfully', 'id': supplier.id}), 201


@token_required
# Update supplier
@suppliers_bp.route('/<int:id>', methods=['PUT'])

def update_supplier(id):
    s = Supplier.query.get_or_404(id)
    data = request.get_json()
    s.name = data.get('name', s.name)
    s.contact = data.get('contact', s.contact)
    s.email = data.get('email', s.email)
    s.status = data.get('status', s.status)
    db.session.commit()
    return jsonify({'message': 'Supplier updated successfully', 'id': s.id})


@token_required
# Delete supplier
@suppliers_bp.route('/<int:id>', methods=['DELETE'])

def delete_supplier(id):
    s = Supplier.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'message': 'Supplier deleted successfully', 'id': id})

# ------------------ Purchase Orders ------------------ #

@token_required
# Get all purchase orders
@suppliers_bp.route('/orders', methods=['GET'])

def get_purchase_orders():
    orders = PurchaseOrder.query.filter(PurchaseOrder.status.in_([1, 2, 3,5,4])).all()
    data = [{
        'id': o.id,
        'supplier_id': o.supplier_id,
        'supplier_name': o.supplier.name if o.supplier else None,
        'invoice_number': o.invoice_number,
        'total_amount': o.total_amount,
        'total_paid': o.total_paid,
        'total_balance': o.total_balance,
        'status': o.status,
        'created_at': o.created_at.strftime("%Y-%m-%d"),
        'purchase_date':o.purchase_date.strftime("%Y-%m-%d")
    } for o in orders]
    return jsonify(data), 200


# @token_required
# # Get purchase order by ID
# @suppliers_bp.route('/orders/<int:id>', methods=['GET'])

# def get_purchase_order(id):
#     po = PurchaseOrder.query.get_or_404(id)
#     return jsonify({
#         'id': po.id,
#         'supplier_id': po.supplier_id,
#         'supplier_name': po.supplier.name if po.supplier else None,
#         'invoice_number': po.invoice_number,
#         'memo': po.memo,
#         'purchase_date': po.purchase_date.strftime("%Y-%m-%d"),
#         'total_amount': po.total_amount,
#         'total_paid': po.total_paid,
#         'total_balance': po.total_balance,
#         'status': po.status,
#         'items': [{
#             'id': item.id,
#             'product_id': item.product_id,
#             'product_name': Product.query.get(item.product_id).name if item.product_id else None,
#             'stock_quantity': Product.query.get(item.product_id).quantity if item.product_id else None,
#             'unit': db.session.query(Category).filter_by(id=Product.query.get(item.product_id).category_id).first().name if item.product_id and Product.query.get(item.product_id) else None,
#             'quantity': item.quantity,
#             'unit_price': item.unit_price,
#             'total_price': item.total_price,
#             'status': item.status
#         } for item in po.items]
#     })

@token_required
@suppliers_bp.route('/orders/<int:id>', methods=['GET'])
def get_purchase_order(id):
    """
    Get detailed purchase order information by ID.
    Includes supplier info, product category, and product unit (e.g., crate, bottle).
    """
    po = PurchaseOrder.query.get_or_404(id)
    print(" herre .. ")

    return jsonify({
        "id": po.id,
        "supplier_id": po.supplier_id,
        "supplier_name": po.supplier.name if po.supplier else None,
        "invoice_number": po.invoice_number,
        "memo": po.memo,
        "purchase_date": po.purchase_date.strftime("%Y-%m-%d") if po.purchase_date else None,
        "total_amount": po.total_amount,
        "total_paid": po.total_paid,
        "total_balance": po.total_balance,
        "status": po.status,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name if (product := Product.query.get(item.product_id)) else None,
                "stock_quantity": product.quantity if product else None,
                # ✅ Include product category
                "category": (
                    db.session.query(Category.name)
                    .filter_by(id=product.category_id, status=1)
                    .scalar()
                    if product and product.category_id else None
                ),
                
                # ✅ Use ProductUnit instead of Category
                "unit_id": item.unit_id,
                "unit_name": (
                    db.session.query(ProductUnit.unit_name)
                    .filter_by(id=item.unit_id)
                    .scalar()
                    if item.unit_id else None
                ),
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "status": item.status,
            }
            for item in po.items
        ],
    })


# this is for the supplier pruchase 

@token_required
# Add new purchase order with multiple items
@suppliers_bp.route('/orders', methods=['POST'])

def add_purchase_order():
    data = request.get_json()

    if not data.get('items') or len(data['items']) == 0:
        return jsonify({'error': 'At least one item is required'}), 400

    # Create new Purchase Order
    po = PurchaseOrder(
        supplier_id=data['supplier_id'],
        invoice_number=data['invoice_number'],
        purchase_date=data.get('purchase_date', datetime.utcnow()),
        memo=data.get('memo'),
        status=1
    )
    db.session.add(po)
    db.session.flush()  # to get PO id before committing

    total_amount = 0
    txn_id, txn_str = generate_transaction_number('CREDIT-PAY',transaction_date=po.purchase_date)
    po.transaction_no=txn_id

    # Add purchase order items
    for item_data in data['items']:
        product_unit= ProductUnit.query.filter_by(id=item_data.get('unit_id')).first()
        quantity=0
        # cost_price=0
        if product_unit:
            if product_unit.conversion_quantity and product_unit.conversion_quantity>1 :
                quantity=item_data['quantity'] * product_unit.conversion_quantity
                # cost_price= round(item_data['cost_price']/product_unit.conversion_quantity,2)
            else:
                quantity=item_data['quantity']
                # cost_price=item_data['cost_price'],
       
        item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            unit_price=item_data['cost_price'],
            unit_id=item_data.get('unit_id'),
            status=1
        )
        item.calculate_total()
        db.session.add(item)
        total_amount += item.total_price

        # Update product stock
        product = Product.query.get(item.product_id)
        if product:
            product.quantity = (product.quantity or 0) + quantity
            db.session.add(product)
            # --- ✅ NEW: Update Crate Stock if Product is Returnable ---
            if item_data['unit_id'] and item_data["is_returnable"]:
                crate = ReturnableContainer.query.filter_by(product_unit_id=item_data['unit_id']).first()
                if crate:
                    crate.total_in_stock = (crate.total_in_stock or 0) + item.quantity
                    crate.total_issued = crate.total_issued or 0
                    crate.total_returned = crate.total_returned or 0
                    db.session.add(crate)
                    
                    db.session.add(ContainerTransaction(
                        container_id=crate.id,
                        transaction_type='Purchase',
                        quantity=item.quantity,
                        unit_value=crate.unit_value or 0,
                        total_value=(crate.unit_value or 0) * item.quantity,
                        purchase_order_id=po.id,
                        status=1
                    ))


        # ✅ Add InventoryTransaction entry
        inv_txn = InventoryTransaction(
            transaction_no=txn_id,
            purchase_order_id=po.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
            transaction_type='Received',
            status=1
        )
        db.session.add(inv_txn)

    # Update totals
    po.total_amount = total_amount
    po.total_balance = total_amount

    entries = [
        {
            "account_id": 1400,  # Stock Inventory
            "transaction_type": "Debit",
            "amount": total_amount
        },
        {
            "account_id": 3000,# Accounts Payable  
            "transaction_type": "Credit",
            "amount": total_amount
        }
    ]

    post_to_ledger(
        entries,
        transaction_no_id=txn_id,
        description=f"Credit for PO #{po.id}",
        transaction_date=po.purchase_date
    )

    db.session.commit()

    return jsonify({'message': 'Purchase Order created successfully', 'po_id': po.id}), 200





# Update purchase order details
@token_required
@suppliers_bp.route('/orders/<int:id>', methods=['PUT'])
def update_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    data = request.get_json()

    po.supplier_id = data.get('supplier_id', po.supplier_id)
    po.invoice_number = data.get('invoice_number', po.invoice_number)
    po.memo = data.get('memo', po.memo)
    po.purchase_date = data.get('purchase_date', po.purchase_date)

    # Update items if provided
    if 'items' in data:
        for item_data in data['items']:
            if 'id' in item_data:
                # Update existing item
                item = PurchaseOrderItem.query.get(item_data['id'])
                if item and item.purchase_order_id == po.id:
                    item.quantity = item_data.get('quantity', item.quantity)
                    item.unit_price = item_data.get('unit_price', item.unit_price)
                    item.calculate_total()
            else:
                # Add new item
                new_item = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    product_id=item_data['product_id'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    status=1
                )
                new_item.calculate_total()
                db.session.add(new_item)



    # Recalculate totals
    po.update_totals()
    db.session.commit()

    return jsonify({'message': 'Purchase Order updated successfully', 'id': po.id})


@token_required
# Delete purchase order
@suppliers_bp.route('/orders/<int:id>', methods=['DELETE'])

def delete_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    db.session.delete(po)
    db.session.commit()
    return jsonify({'message': 'Purchase Order deleted successfully', 'id': id})


@token_required
@suppliers_bp.route('/orders/<int:id>/pay', methods=['POST'])
def pay_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    data = request.get_json()

    amount = data['amount']
    payment_type = data.get('payment_type', 'Cash')
    reference = data.get('reference')
    payment_account_id = data.get('payment_account_id')
    transaction_date_str = data.get('transaction_date')  # <-- New field from frontend

    # Validate transaction date or fallback to UTC now
    try:
        if transaction_date_str:
            # Parse provided date
            transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d')
        else:
            transaction_date = datetime.utcnow()
    except ValueError:
        return jsonify({'error': 'Invalid transaction date format. Use YYYY-MM-DD'}), 400

    if not payment_account_id:
        return jsonify({'error': 'Payment account is required'}), 400

    # Validate payment account exists
    payment_account = Account.query.get(payment_account_id)
    if not payment_account:
        return jsonify({'error': 'Invalid payment account selected'}), 400

    if amount <= 0:
        return jsonify({'error': 'Invalid payment amount'}), 400

    if amount > po.total_balance:
        return jsonify({'error': 'Payment exceeds remaining balance'}), 400

    # ---------- Generate Transaction Number First ----------
    txn_id, txn_str = generate_transaction_number('SUPP-PAY',transaction_date=transaction_date)

    # Create supplier payment record AFTER txn number exists
    payment = SupplierPayment(
        purchase_order_id=po.id,
        payment_account_id=payment_account_id,
        amount=amount,
        payment_type=payment_type,
        reference=reference,
        transaction_no=txn_id,  # ✅ Now guaranteed to exist
        payment_date=transaction_date,
        status=1
    )
    db.session.add(payment)
    db.session.flush()

    # Update PurchaseOrder totals
    po.total_paid += amount
    po.total_balance = po.total_amount - po.total_paid
    po.status = 3 if po.total_balance == 0 else 5 if po.total_paid == po.total_balance else 4

    # ---------- Generate GL Double Entry ----------
    entries = [
        {
            "account_id": 3000,  # Accounts Payable
            "transaction_type": "Debit",
            "amount": amount
        },
        {
            "account_id": payment_account.code,  # Dynamic account
            "transaction_type": "Credit",
            "amount": amount
        }
    ]

    post_to_ledger(
        entries,
        transaction_no_id=txn_id,
        description=f"Payment for PO #{po.id}",
        transaction_date=transaction_date
    )

    # Final commit
    db.session.commit()

    return jsonify({
        "message": f"Payment of {amount} recorded for PO #{po.id}",
        "payment_id": payment.id,
        "new_balance": po.total_balance,
        "po_status": po.status,
        "gl_transaction_id": txn_id
    }), 201




@token_required
@suppliers_bp.route('/orders/<int:id>/edit', methods=['PUT'])
def edit_purchase_order(id):
    """
    Edit an existing purchase order, update items, handle container stock & returns,
    recalc inventory, post GL adjustments, and support soft delete (status=9).
    """
    po = PurchaseOrder.query.get_or_404(id)
    data = request.get_json()

    # --- Handle soft delete of entire PO ---
    if data.get("status") == 9:
        po.status = 9
        # Reverse stock for all items
        for item in po.items:
            product = Product.query.get(item.product_id)
            if product:
                product_unit= ProductUnit.query.filter_by(id=product.unit_id).first()
                quantity=0
                # cost_price=0
                if product_unit :
                    if product_unit.conversion_quantity and product_unit.conversion_quantity>1 :
                        quantity=item.quantity * product_unit.conversion_quantity
                        # cost_price= round(item_data['cost_price']/product_unit.conversion_quantity,2)
                    else:
                        quantity=item.quantity
                        # cost_price=item_data['cost_price'],
                product.quantity = max((product.quantity or 0) - quantity, 0)
                db.session.add(product)

            # Reverse returnable container stock
            if item.unit_id:
                crate = ReturnableContainer.query.filter_by(product_unit_id=item.unit_id).first()
                if crate:
                    crate.total_in_stock = max((crate.total_in_stock or 0) - item.quantity, 0)
                    db.session.add(crate)
                    db.session.add(ContainerTransaction(
                        container_id=crate.id,
                        transaction_type='Removed',
                        quantity=item.quantity,
                        unit_value=crate.cost_price or 0,
                        total_value=(crate.cost_price or 0) * item.quantity,
                        purchase_order_id=po.id,
                        status=9
                    ))

            # Soft delete item
            item.status = 9
            db.session.add(item)

        db.session.add(po)
        db.session.commit()
        return jsonify({"message": f"Purchase Order #{po.id} soft-deleted successfully"}), 200

    old_total = po.total_amount
    old_paid = po.total_paid

    # --- Update PO header ---
    po.supplier_id = data.get('supplier_id', po.supplier_id)
    po.invoice_number = data.get('invoice_number', po.invoice_number)
    po.memo = data.get('memo', po.memo)
    po.purchase_date = data.get('purchase_date', po.purchase_date)

    # --- Process Items ---
    if 'items' in data:
        existing_item_ids = [item.id for item in po.items if item.status != 9]
        new_item_ids = [i.get('id') for i in data['items'] if i.get('id')]

        # --- Soft delete removed items ---
        for item in po.items:
            if item.id not in new_item_ids and item.status != 9:
                item.status = 9  # soft delete
                db.session.add(item)

                # Reverse stock
                product = Product.query.get(item.product_id)
                if product:
                    product_unit= ProductUnit.query.filter_by(id=product.unit_id).first()
                    quantity=0
                    # cost_price=0
                    if product_unit :
                        if product_unit.conversion_quantity and product_unit.conversion_quantity>1 :
                            quantity=item.quantity * product_unit.conversion_quantity
                            # cost_price= round(item_data['cost_price']/product_unit.conversion_quantity,2)
                        else:
                            quantity=item.quantity
                            # cost_price=item_data['cost_price'],

                    product.quantity = max((product.quantity or 0) - quantity, 0)
                    db.session.add(product)

                # Reverse returnable container stock
                if item.unit_id:
                    crate = ReturnableContainer.query.filter_by(product_unit_id=item.unit_id).first()
                    if crate:
                        crate.total_in_stock = max((crate.total_in_stock or 0) - item.quantity, 0)
                        db.session.add(crate)
                        db.session.add(ContainerTransaction(
                            container_id=crate.id,
                            transaction_type='Removed',
                            quantity=item.quantity,
                            unit_value=crate.cost_price or 0,
                            total_value=(crate.cost_price or 0) * item.quantity,
                            purchase_order_id=po.id,
                            status=9
                        ))

        # --- Update or Add new items ---
        for item_data in data['items']:
            product = Product.query.get(item_data['product_id'])
            if not product:
                continue

            if 'id' in item_data and item_data['id']:
                # Update existing item
                item = PurchaseOrderItem.query.get(item_data['id'])
                old_qty = item.quantity
                item.quantity = item_data.get('quantity', item.quantity)
                item.unit_price = item_data.get('unit_price', item.unit_price)
                item.unit_id = item_data.get('unit_id', item.unit_id)
                item.calculate_total()
                db.session.add(item)

                # Update product stock difference
                diff_qty = item.quantity - old_qty
                product_unit= ProductUnit.query.filter_by(id=product.unit_id).first()
                diff_quantity=0
                # cost_price=0
                if product_unit :
                    if product_unit.conversion_quantity and product_unit.conversion_quantity>1 :
                        diff_quantity=diff_qty * product_unit.conversion_quantity
                        # cost_price= round(item_data['cost_price']/product_unit.conversion_quantity,2)
                    else:
                        diff_quantity=diff_qty
                        # cost_price=item_data['cost_price'],
                # product.quantity = (product.quantity or 0) + diff_qty
                product.quantity = (product.quantity or 0) + diff_quantity

                db.session.add(product)

                # Update returnable container stock if applicable
                if item_data.get("is_returnable") and item_data.get("unit_id"):
                    crate = ReturnableContainer.query.filter_by(product_unit_id=item_data["unit_id"]).first()
                    if crate:
                        crate.total_in_stock = (crate.total_in_stock or 0) + diff_qty
                        db.session.add(crate)
                        db.session.add(ContainerTransaction(
                            container_id=crate.id,
                            transaction_type='Adjusted',
                            quantity=diff_qty,
                            unit_value=crate.cost_price or 0,
                            total_value=(crate.cost_price or 0) * diff_qty,
                            purchase_order_id=po.id,
                            status=1
                        ))
            else:
                # Add new item
                new_item = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    product_id=item_data['product_id'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    unit_id=item_data.get('unit_id'),
                    status=1
                )
                new_item.calculate_total()
                db.session.add(new_item)


                # Update product stock
                product_unit= ProductUnit.query.filter_by(id=product.unit_id).first()
                quantity=0
                # cost_price=0
                if product_unit :
                    if product_unit.conversion_quantity and product_unit.conversion_quantity>1 :
                        quantity=new_item.quantity * product_unit.conversion_quantity
                        # cost_price= round(item_data['cost_price']/product_unit.conversion_quantity,2)
                    else:
                        quantity=new_item.quantity
                
                
                # product.quantity = (product.quantity or 0) + new_item.quantity
                product.quantity = (product.quantity or 0) + quantity
                db.session.add(product)

                # Handle returnable container
                if item_data.get("is_returnable") and item_data.get("unit_id"):
                    crate = ReturnableContainer.query.filter_by(product_unit_id=item_data["unit_id"]).first()
                    if crate:
                        crate.total_in_stock = (crate.total_in_stock or 0) + new_item.quantity
                        crate.total_issued = crate.total_issued or 0
                        crate.total_returned = crate.total_returned or 0
                        db.session.add(crate)
                        db.session.add(ContainerTransaction(
                            container_id=crate.id,
                            transaction_type='Purchase',
                            quantity=new_item.quantity,
                            unit_value=crate.cost_price or 0,
                            total_value=(crate.cost_price or 0) * new_item.quantity,
                            purchase_order_id=po.id,
                            status=1
                        ))

                # Inventory transaction
                db.session.add(InventoryTransaction(
                    transaction_no=po.transaction_no,
                    purchase_order_id=po.id,
                    product_id=new_item.product_id,
                    quantity=new_item.quantity,
                    unit_price=new_item.unit_price,
                    total_price=new_item.total_price,
                    transaction_type='Received',
                    status=1
                ))

    # --- Recalculate totals and handle payments ---
    po.update_totals()
    new_total = po.total_amount
    payments = SupplierPayment.query.filter_by(purchase_order_id=po.id, status=1).all()
    total_paid = sum(p.amount for p in payments)

    if total_paid >= new_total:
        po.total_paid = new_total
        po.total_balance = 0
        po.status = 3
    else:
        po.total_paid = total_paid
        po.total_balance = new_total - total_paid
        po.status = 2 if po.total_balance > 0 else 3

    # --- GL adjustments ---
    txn_id, txn_str = generate_transaction_number('PO-EDIT', transaction_date=po.purchase_date)
    diff = new_total - old_total
    if diff != 0:
        if diff > 0:
            entries = [
                {"account_id": 1400, "transaction_type": "Debit", "amount": diff},
                {"account_id": 3000, "transaction_type": "Credit", "amount": diff}
            ]
            desc = f"Adjustment for increased PO #{po.id} by {diff}"
        else:
            entries = [
                {"account_id": 3000, "transaction_type": "Debit", "amount": abs(diff)},
                {"account_id": 1400, "transaction_type": "Credit", "amount": abs(diff)}
            ]
            desc = f"Adjustment for reduced PO #{po.id} by {abs(diff)}"
        post_to_ledger(entries, transaction_no_id=txn_id, description=desc, transaction_date=po.purchase_date)

    db.session.commit()

    return jsonify({
        "message": f"Purchase Order #{po.id} updated successfully",
        "old_total": old_total,
        "new_total": new_total,
        "total_paid": po.total_paid,
        "balance": po.total_balance,
        "status": po.status,
        "gl_transaction_id": txn_id
    }), 200







@token_required
@suppliers_bp.route('/purchase-order/<int:purchase_order_id>', methods=['GET'])

def purchase_order_details(purchase_order_id):
    return get_purchase_order_details(purchase_order_id)




def get_purchase_order_details(purchase_order_id):
    """
    Retrieve complete purchase order details including supplier info,
    items, payments, and financial totals.
    Includes product category and unit details.
    """
    # Fetch the Purchase Order with related Supplier, Items, and Payments
    purchase_order = (
        PurchaseOrder.query
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.items),
            joinedload(PurchaseOrder.supplier).joinedload(Supplier.purchase_orders)
        )
        .filter(PurchaseOrder.id == purchase_order_id, PurchaseOrder.status != 9)
        .first()
    )

    if not purchase_order:
        return {"error": "Purchase order not found or inactive"}, 404

    # Fetch all payments linked to this purchase order
    payments = SupplierPayment.query.filter_by(
        purchase_order_id=purchase_order_id,
        status=1
    ).all()

    # Calculate totals
    total_amount = sum(item.total_price for item in purchase_order.items if item.status != 9)
    total_paid = sum(payment.amount for payment in payments)
    balance = total_amount - total_paid

    # Prepare item details
    item_details = []
    for item in purchase_order.items:
        if item.status == 9:
            continue

        product = Product.query.get(item.product_id) if item.product_id else None
        category_name = None
        category_id = None
        if product and product.category_id:
            category = db.session.query(Category).filter_by(id=product.category_id, status=1).first()
            if category:
                category_name = category.name
                category_id = category.id

        unit_name = (
            db.session.query(ProductUnit.unit_name)
            .filter_by(id=item.unit_id)
            .scalar()
            if item.unit_id else None
        )

        item_details.append({
            "product_id": item.product_id,
            "product_name": product.name if product else None,
            "category_id": category_id,
            "category": category_name,
            "unit_id": item.unit_id,
            "unit_name": unit_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
        })

    # Prepare payment details
    payment_details = [
        {
            "payment_id": p.id,
            "amount": p.amount,
            "payment_type": p.payment_type,
            "payment_date": p.payment_date.strftime("%Y-%m-%d") if p.payment_date else None,
            "reference": p.reference,
            "account_name": Account.query.get(p.payment_account_id).name if p.payment_account_id else None,
        }
        for p in payments
    ]

    # Final response
    response = {
        "purchase_order_id": purchase_order.id,
        "invoice_number": purchase_order.invoice_number,
        "purchase_date": purchase_order.purchase_date.strftime("%Y-%m-%d") if purchase_order.purchase_date else None,
        "supplier": {
            "supplier_id": purchase_order.supplier.id if purchase_order.supplier else None,
            "name": purchase_order.supplier.name if purchase_order.supplier else None,
            "contact": purchase_order.supplier.contact if purchase_order.supplier else None,
            "email": purchase_order.supplier.email if purchase_order.supplier else None,
        },
        "items": item_details,
        "payments": payment_details,
        "summary": {
            "total_amount": total_amount,
            "total_paid": total_paid,
            "balance": balance,
            "grand_total": total_amount  # extend with tax, discounts later
        }
    }

    return jsonify(response)
