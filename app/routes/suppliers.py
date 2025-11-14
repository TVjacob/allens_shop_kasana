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
from app.models import Account, Category, ContainerTransaction, GeneralLedger, InventoryTransaction, Product, ProductUnit, ReturnableContainer, Supplier, PurchaseOrder, PurchaseOrderItem, SupplierPayment
from app.utils.auth import token_required
from app.utils.gl_utils import get_latest_purchase_price, post_to_ledger, generate_transaction_number
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


@token_required
# Get all purchase orders with search & date filters
@suppliers_bp.route('/orders', methods=['GET'])
def get_purchase_orders():
    # Get query params
    search = request.args.get('search', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    query = PurchaseOrder.query.join(Supplier).filter(PurchaseOrder.status.in_([1,2,3,4,5]))

    # Search filter
    if search:
        search_pattern = f"%{search.lower()}%"
        query = query.filter(
            db.or_(
                db.func.lower(Supplier.name).like(search_pattern),
                db.func.lower(PurchaseOrder.invoice_number).like(search_pattern),
                db.func.lower(PurchaseOrder.memo).like(search_pattern)
            )
        )

    # Date filter
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(PurchaseOrder.purchase_date >= start_dt)
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD."}), 400

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(PurchaseOrder.purchase_date <= end_dt)
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD."}), 400

    orders = query.all()

    data = [{
        'id': o.id,
        'supplier_id': o.supplier_id,
        'supplier_name': o.supplier.name if o.supplier else None,
        'invoice_number': o.invoice_number,
        'memo': o.memo,
        'total_amount': o.total_amount,
        'total_paid': o.total_paid,
        'total_balance': o.total_balance,
        'status': o.status,
        'created_at': o.created_at.strftime("%Y-%m-%d"),
        'purchase_date': o.purchase_date.strftime("%Y-%m-%d"),
        'items': [
            {
                'id': item.id,
                'product_id': item.product_id,
                'product_name': item.product.name if item.product else None,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'total_price': item.total_price
            } for item in o.items
        ]
    } for o in orders]

    return jsonify(data), 200


@token_required
@suppliers_bp.route('/orders/full_details/<int:id>', methods=['GET'])
def get_purchase_order_fill_details(id):
    """
    Return detailed Purchase Order data for editing on frontend.
    Includes:
    - Supplier info
    - Product + category info
    - Product units (with cost/wholesale/retail)
    - Returnable container flags
    """

    po = PurchaseOrder.query.get_or_404(id)

    # --- Fetch supplier info ---
    supplier = Supplier.query.get(po.supplier_id)

    # --- Build item details ---
    items_data = []
    for item in po.items:
        if item.status != 1:
            continue

        product = Product.query.get(item.product_id)
        if not product:
            continue

        # Get category name
        category_name = (
            db.session.query(Category.name)
            .filter_by(id=product.category_id, status=1)
            .scalar()
            if product.category_id else None
        )

        # Get all units for this product
        product_units = ProductUnit.query.filter_by(product_id=product.id).all()
        units_list = [
            {
                "id": u.id,
                "unit_name": u.unit_name,
                "conversion_quantity": u.conversion_quantity,
                "cost_price": u.cost_price,
                "wholesale_price": u.wholesale_price,
                "retail_price": u.retail_price,
                "is_returnable": u.is_returnable,
                "unit_code": u.unit_code
            } for u in product_units
        ]

        # Find current unit
        unit = ProductUnit.query.get(item.unit_id) if item.unit_id else None

        # Returnable info
        container = None
        if unit and unit.is_returnable:
            container = (
                ReturnableContainer.query.filter_by(product_unit_id=unit.id).first()
            )
            container = {
                "id": container.id,
                "total_in_stock": container.total_in_stock,
                "unit_value": container.unit_value
            } if container else None
        last_purchase_price=get_latest_purchase_price(item.product_id)

        items_data.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": product.name,
            "category": category_name,
            "stock_qty": product.quantity or 0,
            "unit_id": item.unit_id,
            "unit_name": unit.unit_name if unit else None,
            "units": units_list,
            "last_purchase_price":last_purchase_price,

            "quantity": item.quantity,
            "cost_price": item.unit_price,
            "wholesale_price": unit.wholesale_price if unit else 0,
            "retail_price": unit.retail_price if unit else 0,
            "total_price": item.total_price,
            "is_returnable": unit.is_returnable if unit else False,
            "container": container,
            "conversion_quantity": unit.conversion_quantity if unit else 1,
            "status": item.status
        })

    return jsonify({
        "id": po.id,
        "supplier_id": po.supplier_id,
        "supplier_name": supplier.name if supplier else None,
        "invoice_number": po.invoice_number,
        "memo": po.memo or "",
        "purchase_date": po.purchase_date.strftime("%Y-%m-%d") if po.purchase_date else None,
        "total_amount": po.total_amount,
        "total_paid": po.total_paid,
        "total_balance": po.total_balance,
        "status": po.status,
        "items": items_data
    })


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



@token_required
@suppliers_bp.route('/orders/<int:id>/soft-delete', methods=['DELETE'])
def soft_delete_purchase_order(id):
    """
    Soft delete a purchase order, reverse product stock, container stock,
    mark all PurchaseOrderItems as status=9, reverse inventory transactions,
    mark payments as voided, and reverse GL entries for the PO and related payments.
    """
    try:
        po = PurchaseOrder.query.get_or_404(id)

        if po.status == 9:
            return jsonify({'message': f'Purchase Order #{po.id} already deleted'}), 400

        txn_id = po.transaction_no  # Original transaction number for reference

        # -----------------------------
        # STEP 1: Reverse stock and soft-delete PO items
        # -----------------------------
        for item in po.items:
            if item.status == 9:
                continue

            # Reverse product stock
            product = Product.query.get(item.product_id)
            if product:
                product_unit = ProductUnit.query.filter_by(id=item.unit_id).first()
                quantity = item.quantity
                if product_unit and product_unit.conversion_quantity:
                    quantity *= product_unit.conversion_quantity
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
                        unit_value=crate.unit_value or 0,
                        total_value=(crate.unit_value or 0) * item.quantity,
                        purchase_order_id=po.id,
                        status=9
                    ))

            # Soft delete the PurchaseOrderItem
            item.status = 9
            db.session.add(item)

        # -----------------------------
        # STEP 2: Reverse inventory transactions
        # -----------------------------
        inv_txns = InventoryTransaction.query.filter_by(transaction_no=txn_id, status=1).all()
        for inv in inv_txns:
            inv.status = 9
            db.session.add(inv)

        # -----------------------------
        # STEP 3: Soft delete payments
        # -----------------------------
        payments = SupplierPayment.query.filter_by(purchase_order_id=po.id, status=1).all()
        for payment in payments:
            payment.status = 9
            db.session.add(payment)

        # -----------------------------
        # STEP 4: Reverse GL entries
        # -----------------------------
        ledger_txns = GeneralLedger.query.filter(
            ((GeneralLedger.description.ilike(f"%Credit for PO #{po.id}%")) |
             (GeneralLedger.description.ilike(f"%Payment for PO #{po.id}%"))) &
            (GeneralLedger.status == 1)
        ).all()

        for gl in ledger_txns:
            # Mark original GL entry as deleted
            # gl.status = 9
            # db.session.add(gl)

            # Create reversal GL entry (debit ↔ credit)
            reversed_entry = GeneralLedger(
                transaction_no=gl.transaction_no,
                account_id=gl.account_id,
                transaction_type="Debit" if gl.transaction_type == "Credit" else "Credit",
                amount=gl.amount,
                description=f"Reversal of {gl.description}",
                transaction_date=datetime.utcnow(),
                status=1
            )
            db.session.add(reversed_entry)

        # -----------------------------
        # STEP 5: Mark PurchaseOrder as deleted
        # -----------------------------
        po.status = 9
        db.session.add(po)

        db.session.commit()

        return jsonify({
            "message": f"Purchase Order #{po.id} and related items/payments soft-deleted successfully",
            "items_deleted": len(po.items),
            "payments_voided": len(payments),
            "ledger_reversed": len(ledger_txns)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500




@token_required
@suppliers_bp.route('/orders/<int:id>', methods=['PUT'])
def update_purchase_order(id):
    """
    Update an existing Purchase Order:
    - update header
    - sync items (add/update/remove)
    - sync payments (add/update/remove) and post/reverse GL
    - update inventory, returnable containers, inventory transactions
    - post ledger adjustments and reversals
    """
    try:
        data = request.get_json()
        po = PurchaseOrder.query.get_or_404(id)

        if po.status == 9:
            return jsonify({'error': 'Cannot update a deleted purchase order'}), 400

        # --- Update PO header ---
        po.supplier_id = data.get('supplier_id', po.supplier_id)
        po.invoice_number = data.get('invoice_number', po.invoice_number)
        po.memo = data.get('memo', po.memo)
        po.purchase_date = data.get('purchase_date', po.purchase_date)
        db.session.add(po)

        # Ensure transaction number exists for PO (use existing or generate)
        if not po.transaction_no:
            txn_id, txn_str = generate_transaction_number('CREDIT-PAY', transaction_date=po.purchase_date)
            po.transaction_no = txn_id
        txn_id = po.transaction_no

        # ---- ITEMS: prepare maps for existing/new/removed ----
        incoming_items = data.get('items', []) or []
        incoming_item_ids = {it.get('id') for it in incoming_items if it.get('id')}
        existing_items = [it for it in po.items if it.status != 9]
        existing_item_map = {it.id: it for it in existing_items}

        total_amount = 0.0

        # 1) Soft-delete items removed from the update (and reverse their effects)
        for old_item in existing_items:
            if old_item.id not in incoming_item_ids:
                # Reverse product stock
                product = Product.query.get(old_item.product_id)
                product_unit = ProductUnit.query.filter_by(id=old_item.unit_id).first()
                qty_to_reverse = old_item.quantity
                if product_unit and (product_unit.conversion_quantity or 1) > 1:
                    qty_to_reverse = old_item.quantity * (product_unit.conversion_quantity or 1)
                if product:
                    product.quantity = max((product.quantity or 0) - qty_to_reverse, 0)
                    db.session.add(product)

                # Reverse returnable container stock
                if old_item.unit_id:
                    crate = ReturnableContainer.query.filter_by(product_unit_id=old_item.unit_id).first()
                    if crate:
                        crate.total_in_stock = max((crate.total_in_stock or 0) - old_item.quantity, 0)
                        db.session.add(crate)
                        db.session.add(ContainerTransaction(
                            container_id=crate.id,
                            transaction_type='Removed',
                            quantity=old_item.quantity,
                            unit_value=crate.unit_value or 0,
                            total_value=(crate.unit_value or 0) * old_item.quantity,
                            purchase_order_id=po.id,
                            status=9
                        ))

                # Soft-delete associated inventory transactions (by purchase_order_id+product)
                inv_txns = InventoryTransaction.query.filter_by(
                    purchase_order_id=po.id, product_id=old_item.product_id, status=1
                ).all()
                for inv in inv_txns:
                    inv.status = 9
                    db.session.add(inv)

                # Reverse GL entries that explicitly reference this PO (keep original approach consistent)
                gl_entries = GeneralLedger.query.filter(
                    GeneralLedger.description.ilike(f"%Credit for PO #{po.id}%"),
                    GeneralLedger.status == 1
                ).all()
                for gl in gl_entries:
                    # mark original as voided (optional) and add reversal entry
                    # gl.status = 9
                    # db.session.add(gl)
                    reversed = GeneralLedger(
                        transaction_no=gl.transaction_no,
                        account_id=gl.account_id,
                        transaction_type="Debit" if gl.transaction_type == "Credit" else "Credit",
                        amount=gl.amount,
                        description=f"Reversal of {gl.description}",
                        transaction_date=datetime.utcnow(),
                        status=1
                    )
                    db.session.add(reversed)

                # Soft delete the item
                old_item.status = 9
                db.session.add(old_item)

        # 2) Iterate incoming items: update existing or add new ones
        for it in incoming_items:
            # map names chosen in incoming payload: cost_price or unit_price? use cost_price as earlier
            item_id = it.get('id')
            product_id = it.get('product_id')
            unit_id = it.get('unit_id')
            new_qty = int(it.get('quantity', 0))
            cost_price = float(it.get('cost_price', it.get('unit_price', 0)))

            if item_id:  # update existing
                item = PurchaseOrderItem.query.get(item_id)
                if not item or item.status == 9:
                    continue

                old_qty = item.quantity or 0
                old_unit_id = item.unit_id
                old_unit = ProductUnit.query.filter_by(id=old_unit_id).first() if old_unit_id else None

                # compute stock difference (consider conversion quantities)
                convert = 1
                if old_unit and (old_unit.conversion_quantity or 1) > 1:
                    convert = old_unit.conversion_quantity
                diff_qty = new_qty - old_qty
                stock_adjustment = diff_qty * convert

                # apply to product
                product = Product.query.get(item.product_id)
                if product:
                    product.quantity = (product.quantity or 0) + stock_adjustment
                    db.session.add(product)

                # update item values
                item.quantity = new_qty
                item.unit_price = cost_price
                item.unit_id = unit_id or item.unit_id
                item.calculate_total()
                db.session.add(item)

                # inventory transaction: update or create
                inv_txn = InventoryTransaction.query.filter_by(purchase_order_id=po.id,
                                                              product_id=item.product_id,
                                                              status=1).first()
                if inv_txn:
                    inv_txn.quantity = item.quantity
                    inv_txn.unit_price = item.unit_price
                    inv_txn.total_price = item.total_price
                    db.session.add(inv_txn)
                else:
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

                # container adjustments if flagged
                if it.get('is_returnable') and item.unit_id:
                    crate = ReturnableContainer.query.filter_by(product_unit_id=item.unit_id).first()
                    if crate:
                        crate.total_in_stock = (crate.total_in_stock or 0) + diff_qty
                        db.session.add(crate)
                        db.session.add(ContainerTransaction(
                            container_id=crate.id,
                            transaction_type='Purchase Adjustment',
                            quantity=diff_qty,
                            unit_value=crate.unit_value or 0,
                            total_value=(crate.unit_value or 0) * diff_qty,
                            purchase_order_id=po.id,
                            status=1
                        ))

                total_amount += item.total_price

            else:  # new item
                product_unit = ProductUnit.query.filter_by(id=unit_id).first()
                convert_qty = product_unit.conversion_quantity if product_unit else 1
                stock_increase = new_qty * (convert_qty or 1)

                new_item = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    product_id=product_id,
                    quantity=new_qty,
                    unit_price=cost_price,
                    unit_id=unit_id,
                    status=1
                )
                new_item.calculate_total()
                db.session.add(new_item)
                db.session.flush()  # to get id if needed

                # update product stock
                product = Product.query.get(product_id)
                if product:
                    product.quantity = (product.quantity or 0) + stock_increase
                    db.session.add(product)

                # handle returnable containers
                if it.get('is_returnable') and unit_id:
                    crate = ReturnableContainer.query.filter_by(product_unit_id=unit_id).first()
                    if crate:
                        crate.total_in_stock = (crate.total_in_stock or 0) + new_item.quantity
                        db.session.add(crate)
                        db.session.add(ContainerTransaction(
                            container_id=crate.id,
                            transaction_type='Purchase',
                            quantity=new_item.quantity,
                            unit_value=crate.unit_value or 0,
                            total_value=(crate.unit_value or 0) * new_item.quantity,
                            purchase_order_id=po.id,
                            status=1
                        ))

                # create inventory transaction
                inv_txn = InventoryTransaction(
                    transaction_no=txn_id,
                    purchase_order_id=po.id,
                    product_id=new_item.product_id,
                    quantity=new_item.quantity,
                    unit_price=new_item.unit_price,
                    total_price=new_item.total_price,
                    transaction_type='Received',
                    status=1
                )
                db.session.add(inv_txn)

                total_amount += new_item.total_price

        # -----------------------------
        # PAYMENTS: sync payments if provided
        # incoming payments payload structure:
        # payments: [{ id?, amount, payment_date, payment_account_id, payment_type, reference }]
        # -----------------------------
        incoming_payments = data.get('payments', None)
        if incoming_payments is not None:
            # Build maps for existing payments
            existing_payments = SupplierPayment.query.filter_by(purchase_order_id=po.id).all()
            existing_payment_map = {p.id: p for p in existing_payments if p.status == 1}

            incoming_payment_ids = {p.get('id') for p in incoming_payments if p.get('id')}

            # 1) Soft-delete removed payments
            for p in existing_payments:
                if p.id not in incoming_payment_ids and p.status == 1:
                    # void payment
                    # p.status = 9
                    # db.session.add(p)
                    # Reverse GL entries related to this payment
                    gl_payments = GeneralLedger.query.filter(
                        GeneralLedger.description.ilike(f"%Payment for PO #{po.id}%"),
                        GeneralLedger.transaction_no == p.transaction_no,
                        GeneralLedger.status == 1
                    ).all()
                    for gl in gl_payments:
                        gl.status = 9
                        db.session.add(gl)
                        reversed_entry = GeneralLedger(
                            transaction_no=gl.transaction_no,
                            account_id=gl.account_id,
                            transaction_type="Debit" if gl.transaction_type == "Credit" else "Credit",
                            amount=gl.amount,
                            description=f"Reversal of {gl.description}",
                            transaction_date=datetime.utcnow(),
                            status=1
                        )
                        db.session.add(reversed_entry)

            # 2) Update existing payments (if amount changed): create reversal then new GL
            for inc in incoming_payments:
                pid = inc.get('id')
                if pid and pid in existing_payment_map:
                    p = existing_payment_map[pid]
                    new_amount = float(inc.get('amount', p.amount))
                    # if amount changed -> reverse original GL and post new GL
                    if abs(new_amount - (p.amount or 0)) > 0.0001:
                        # mark original payment as replaced (soft-void)
                        p.status = 9
                        db.session.add(p)

                        # reverse original GL
                        gls = GeneralLedger.query.filter(
                            GeneralLedger.transaction_no == p.transaction_no,
                            GeneralLedger.status == 1
                        ).all()
                        for gl in gls:
                            # gl.status = 9
                            # db.session.add(gl)
                            db.session.add(GeneralLedger(
                                transaction_no=gl.transaction_no,
                                account_id=gl.account_id,
                                transaction_type="Debit" if gl.transaction_type == "Credit" else "Credit",
                                amount=gl.amount,
                                description=f"Reversal of {gl.description}",
                                transaction_date=datetime.utcnow(),
                                status=1
                            ))

                        # create new payment record with new txn_no and GL
                        tx_id, tx_str = generate_transaction_number('SUPP-PAY', transaction_date=datetime.utcnow())
                        new_p = SupplierPayment(
                            purchase_order_id=po.id,
                            payment_account_id=inc.get('payment_account_id'),
                            amount=new_amount,
                            payment_type=inc.get('payment_type', p.payment_type),
                            reference=inc.get('reference', p.reference),
                            transaction_no=tx_id,
                            payment_date=datetime.strptime(inc.get('payment_date'), '%Y-%m-%d') if inc.get('payment_date') else datetime.utcnow(),
                            status=1
                        )
                        db.session.add(new_p)

                        # post GL for new payment
                        acc = Account.query.get(new_p.payment_account_id)
                        entries = [
                            {"account_id": 3000, "transaction_type": "Debit", "amount": new_amount},  # AP
                            {"account_id": acc.code if acc else 1100, "transaction_type": "Credit", "amount": new_amount}
                        ]
                        post_to_ledger(entries, transaction_no_id=tx_id,
                                       description=f"Payment for PO #{po.id}", transaction_date=new_p.payment_date)

                elif not pid:
                    # New payment -> create and post GL
                    new_amount = float(inc.get('amount', 0))
                    if new_amount <= 0:
                        continue
                    tx_id, tx_str = generate_transaction_number('SUPP-PAY', transaction_date=datetime.strptime(inc.get('payment_date'), '%Y-%m-%d') if inc.get('payment_date') else datetime.utcnow())
                    new_p = SupplierPayment(
                        purchase_order_id=po.id,
                        payment_account_id=inc.get('payment_account_id'),
                        amount=new_amount,
                        payment_type=inc.get('payment_type', 'Cash'),
                        reference=inc.get('reference'),
                        transaction_no=tx_id,
                        payment_date=datetime.strptime(inc.get('payment_date'), '%Y-%m-%d') if inc.get('payment_date') else datetime.utcnow(),
                        status=1
                    )
                    db.session.add(new_p)
                    # post GL
                    acc = Account.query.get(new_p.payment_account_id)
                    entries = [
                        {"account_id": 3000, "transaction_type": "Debit", "amount": new_amount},
                        {"account_id": acc.code if acc else 1100, "transaction_type": "Credit", "amount": new_amount}
                    ]
                    post_to_ledger(entries, transaction_no_id=tx_id,
                                   description=f"Payment for PO #{po.id}", transaction_date=new_p.payment_date)

        # -----------------------------
        # FINAL: recompute totals and post PO GL adjustment
        # -----------------------------
        # Recompute total_amount from active items
        total_amount = sum(i.total_price for i in po.items if i.status != 9)
        # Recompute total_paid from active payments
        total_paid = sum(p.amount for p in SupplierPayment.query.filter_by(purchase_order_id=po.id, status=1).all())
        po.total_amount = total_amount
        po.total_paid = total_paid
        po.total_balance = max(po.total_amount - po.total_paid, 0)

        # set PO status (1=Ready/invoice, 2=Partially paid, 3=Paid, 4/5 other states)
        if po.total_balance == 0:
            po.status = 3
        elif po.total_paid > 0:
            po.status = 2
        else:
            po.status = 1

        db.session.add(po)

        # Post an updated PO GL (create new ledger entry to reflect updated totals)
        # Use new txn number for the PO update
        update_txn_id, update_txn_str = generate_transaction_number('PO-EDIT', transaction_date=po.purchase_date)
        entries = [
            {"account_id": 1400, "transaction_type": "Debit", "amount": po.total_amount},
            {"account_id": 3000, "transaction_type": "Credit", "amount": po.total_amount},
        ]
        post_to_ledger(entries, transaction_no_id=update_txn_id,
                       description=f"Updated Credit for PO #{po.id}", transaction_date=po.purchase_date)

        db.session.commit()

        return jsonify({
            "message": f"Purchase Order #{po.id} updated successfully",
            "po_id": po.id,
            "total_amount": po.total_amount,
            "total_paid": po.total_paid,
            "total_balance": po.total_balance,
            "status": po.status
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# # Update purchase order details
# @token_required
# @suppliers_bp.route('/orders/<int:id>', methods=['PUT'])
# def update_purchase_order(id):
#     po = PurchaseOrder.query.get_or_404(id)
#     data = request.get_json()

#     po.supplier_id = data.get('supplier_id', po.supplier_id)
#     po.invoice_number = data.get('invoice_number', po.invoice_number)
#     po.memo = data.get('memo', po.memo)
#     po.purchase_date = data.get('purchase_date', po.purchase_date)

#     # Update items if provided
#     if 'items' in data:
#         for item_data in data['items']:
#             if 'id' in item_data:
#                 # Update existing item
#                 item = PurchaseOrderItem.query.get(item_data['id'])
#                 if item and item.purchase_order_id == po.id:
#                     item.quantity = item_data.get('quantity', item.quantity)
#                     item.unit_price = item_data.get('unit_price', item.unit_price)
#                     item.calculate_total()
#             else:
#                 # Add new item
#                 new_item = PurchaseOrderItem(
#                     purchase_order_id=po.id,
#                     product_id=item_data['product_id'],
#                     quantity=item_data['quantity'],
#                     unit_price=item_data['unit_price'],
#                     status=1
#                 )
#                 new_item.calculate_total()
#                 db.session.add(new_item)



#     # Recalculate totals
#     po.update_totals()
#     db.session.commit()

#     return jsonify({'message': 'Purchase Order updated successfully', 'id': po.id})


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

    # --- Recalculate totals correctly ---
    po.update_totals()

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
