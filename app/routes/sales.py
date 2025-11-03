from flask import Blueprint, request, jsonify
from app import db
from app.models import Account, BottleTransaction, Category, ContainerTransaction, Customer, InventoryTransaction, Payment, Product, ProductUnit, PurchaseOrderItem, ReturnableContainer, Sale, SaleItem, GeneralLedger
from app.utils.auth import token_required
from app.utils.gl_utils import post_to_ledger, generate_transaction_number_partone,generate_transaction_number
from datetime import datetime

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

# ------------------ Helper function for updating timestamps ------------------ #
def update_timestamps(obj):
    obj.updated_at = datetime.utcnow()
    if not obj.created_at:
        obj.created_at = datetime.utcnow()

@token_required
@sales_bp.route('/', methods=['POST'])
def create_sale():
    data = request.json

    try:
        items = data.get('items', [])
        amount_paid = float(data.get('amount_paid', 0))
        payment_account_id = data.get('payment_account_id')
        sale_date_str = data.get("sale_date")
        payment_type = data.get('payment_type', 'Cash')

        # --- Validation: Items ---
        if not items:
            return jsonify({"error": "At least one item is required"}), 400

        # --- Validation: Sale date ---
        try:
            sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d") if sale_date_str else datetime.utcnow()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # --- Initialize totals ---
        total_amount = 0
        cogs_total = 0
        txn_id, txn_str = generate_transaction_number_partone('INV', transaction_date=sale_date)

        # --- Create Sale record ---
        sale = Sale(
            sale_number=txn_str,
            customer_id=data.get("customer_id", 1),
            total_paid=amount_paid,
            status=1,
            sale_date=sale_date
        )
        db.session.add(sale)
        db.session.flush()

        # --- Process Sale Items ---
        for idx, item_data in enumerate(items, start=1):
            product_id = item_data.get("product_id")
            unit_id = item_data.get("unit_id")
            quantity = float(item_data.get("quantity", 0))
            unit_price = float(item_data.get("unit_price", 0))
            total_price = float(item_data.get("total_price", unit_price * quantity))

            # --- Validation ---
            if not product_id or not unit_id:
                return jsonify({"error": f"Product ID and Unit ID are required for item #{idx}"}), 400

            product = Product.query.get(product_id)
            if not product:
                return jsonify({"error": f"Product with ID {product_id} not found for item #{idx}"}), 404

            unit = ProductUnit.query.get(unit_id)
            if not unit or unit.product_id != product.id:
                return jsonify({"error": f"Invalid unit {unit_id} for product {product.name}"}), 400

            # --- Compute consumption quantity ---
            consumption_qty = quantity * unit.conversion_quantity

            # --- Check stock availability ---
            if product.quantity < consumption_qty:
                return jsonify({
                    "error": f"Insufficient stock for {product.name}. Required {consumption_qty}, available {product.quantity}"
                }), 400

            # --- Returnable container handling ---
            if unit.is_returnable:
                container = ReturnableContainer.query.filter_by(product_unit_id=unit.id).first()
                container_id = None
                if container:
                    container.process_transaction('Issued', quantity)
                    db.session.add(container)

                    cont_txn = ContainerTransaction(
                        container_id=container.id,
                        sale_id=sale.id,
                        customer_id=sale.customer_id,
                        transaction_type='Issued',
                        quantity=quantity,
                        unit_value=unit.cost_price or 0,
                        status=1
                    )
                    cont_txn.calculate_total_value()
                    db.session.add(cont_txn)
                    container_id = container.id

                product_unit_bottle = ProductUnit.query.filter_by(product_id=product_id, conversion_quantity=1).first()
                bottle_txn = BottleTransaction(
                    container_id=container_id,
                    product_unit_id=unit.id,
                    sale_id=sale.id,
                    transaction_type='Issued',
                    quantity=consumption_qty,
                    unit_value=product_unit_bottle.cost_price if product_unit_bottle else 0,
                    status=1
                )
                bottle_txn.calculate_total_value()
                db.session.add(bottle_txn)

            # --- Record inventory transaction ---
            db.session.add(InventoryTransaction(
                transaction_no=txn_id,
                product_id=product.id,
                purchase_order_id=None,
                quantity=consumption_qty,
                unit_price=unit_price,
                total_price=total_price,
                transaction_type='Sale',
                status=1
            ))

            # --- Reduce stock ---
            product.quantity -= consumption_qty
            db.session.add(product)

            # --- Get latest purchase price ---
            latest_purchase = (
                PurchaseOrderItem.query
                .filter(PurchaseOrderItem.product_id == product.id,PurchaseOrderItem.unit_id== unit_id)
                .order_by(PurchaseOrderItem.created_at.desc())
                .first()
            )
            purchase_price = latest_purchase.unit_price if latest_purchase else 0.0
            cogs_total += purchase_price * consumption_qty
            total_amount += total_price

            # --- Create SaleItem ---
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                unit_id=unit_id,
                status=1
            )
            db.session.add(sale_item)

        # --- Final Sale calculations ---
        sale.total_amount = total_amount
        sale.balance = total_amount - amount_paid
        if amount_paid == 0:
            sale.status = 3  # Credit
        elif 0 < amount_paid < total_amount:
            sale.status = 4  # Partial
        else:
            sale.status = 1  # Paid
        db.session.flush()

        # --- Ledger Posting ---
        credit_account_code = 1100  # default
        if payment_account_id:
            payment_account = Account.query.get(payment_account_id)
            if not payment_account:
                return jsonify({"error": "Invalid payment account"}), 400
            credit_account_code = payment_account.code

        entries = []
        if amount_paid > 0:
            if amount_paid >= total_amount:
                entries = [
                    {"account_id": credit_account_code, "transaction_type": "Debit", "amount": amount_paid},
                    {"account_id": 4010, "transaction_type": "Credit", "amount": amount_paid}, # sales revenus
                    {"account_id": 5010, "transaction_type": "Debit", "amount": cogs_total},#cogs
                    {"account_id": 1400, "transaction_type": "Credit", "amount": cogs_total},#inventory
                ]
            else:
                entries = [
                    {"account_id": credit_account_code, "transaction_type": "Debit", "amount": amount_paid},
                    {"account_id": 1100, "transaction_type": "Debit", "amount": total_amount - amount_paid},
                    {"account_id": 4010, "transaction_type": "Credit", "amount": total_amount},
                    {"account_id": 5010, "transaction_type": "Debit", "amount": cogs_total},
                    {"account_id": 1400, "transaction_type": "Credit", "amount": cogs_total},
                ]
        else:
            entries = [
                {"account_id": 1100, "transaction_type": "Debit", "amount": total_amount},
                {"account_id": 4010, "transaction_type": "Credit", "amount": total_amount},
                {"account_id": 5010, "transaction_type": "Debit", "amount": cogs_total},
                {"account_id": 1400, "transaction_type": "Credit", "amount": cogs_total},
            ]

        gl_entries = post_to_ledger(entries, transaction_no_id=txn_id,
                                    description=f"Sale #{sale.id}", transaction_date=sale_date)
        sale.transaction_no = txn_id

        # --- Payment Record ---
        if amount_paid > 0:
            payment = Payment(
                sale_id=sale.id,
                amount=amount_paid,
                payment_type=payment_type,
                reference=data.get("memo", txn_str),
                payment_date=sale_date,
                payment_account_id=payment_account_id,
                status=1,
                transaction_no=txn_id
            )
            db.session.add(payment)

        db.session.commit()

        return jsonify({
            "message": "Sale created successfully",
            "sale_id": sale.id,
            "total_amount": sale.total_amount,
            "total_paid": sale.total_paid,
            "balance": sale.balance,
            "payment_status": sale.status,
            "transaction_no": txn_str,
            "sale_date": sale.sale_date.strftime("%Y-%m-%d")
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ------------------ Get All Sales ------------------ #
@token_required
@sales_bp.route('/', methods=['GET'])
def get_sales():
    """
    Retrieve all active sales with their customer details and sale items.
    """
    try:
        sales = (
            Sale.query
            .filter(Sale.status.in_([1, 2, 3, 4]))
            .order_by(Sale.id.desc())
            .all()
        )

        data = []
        for s in sales:
            # --- Get customer info ---
            customer = s.customer  # assuming relationship Sale -> Customer exists
            customer_data = {
                "id": customer.id if customer else None,
                "name": customer.name if customer else "Unknown",
                "mobile": getattr(customer, "mobile", None),
                "email": getattr(customer, "email", None),
                "address": getattr(customer, "address", None),
            }

            # --- Get sale items ---
            sale_items = SaleItem.query.filter_by(sale_id=s.id, status=1).all()
            items = [
                {
                    "product_id": i.product_id,
                    "product_name": i.product_name,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "total_price": i.total_price,
                }
                for i in sale_items
            ]

            # --- Append final record ---
            data.append({
                "sale_id": s.id,
                "sale_number": s.sale_number,
                "total_amount": s.total_amount,
                "payment_status": s.payment_status,
                "sale_date": s.sale_date,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "balance": s.balance,
                "total_paid": s.total_paid,
                "customer": customer_data,
                "items": items,
            })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# ------------------ Get Single Sale ------------------ #
@token_required
@sales_bp.route('/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    sale_items = SaleItem.query.filter_by(sale_id=sale.id, status=1).all()

    items = [{
        "product_id": i.product_id,
        "product_name": i.product_name,
        "quantity": i.quantity,
        "unit_price": i.unit_price,
        "total_price": i.total_price
    } for i in sale_items]

    return jsonify({
        "sale_id": sale.id,
        "sale_number": sale.sale_number,
        "total_amount": sale.total_amount,
        "payment_status": sale.payment_status,
        "sale_date": sale.sale_date,
        "created_at": sale.created_at,
        "updated_at": sale.updated_at,
        "items": items
    })


# ------------------ Update Sale ------------------ #
@token_required
@sales_bp.route('/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    data = request.json
    new_items = data.get('items')

    # Reverse old GL entries
    if sale.transaction_no:
        original_entries = GeneralLedger.query.filter_by(transaction_no=sale.transaction_no).all()
        for entry in original_entries:
            reverse_type = 'Credit' if entry.transaction_type == 'Debit' else 'Debit'
            reverse_entry = GeneralLedger(
                account_id=entry.account_id,
                transaction_type=reverse_type,
                amount=entry.amount,
                description=f"Reversal of {entry.description} before update",
                transaction_date=datetime.utcnow(),
                transaction_no=entry.transaction_no
            )
            db.session.add(reverse_entry)

    # Update Sale main fields
    sale.sale_number = data.get('sale_number', sale.sale_number)
    sale.payment_status = data.get('payment_status', sale.payment_status)
    update_timestamps(sale)

    # Update sale items
    if new_items:
        # Restore stock from old items
        for item in sale.saleitem_set:
            product = Product.query.get(item.product_id)
            if product:
                product.quantity += item.quantity
                db.session.add(product)
            db.session.delete(item)

        # Add new items
        total_amount = 0
        for item in new_items:
            product = Product.query.get(item['product_id'])
            if not product:
                return jsonify({"error": f"Product {item['product_id']} not found"}), 404
            if product.quantity < item['quantity']:
                return jsonify({"error": f"Insufficient stock for {product.name}"}), 400

            product.quantity -= item['quantity']
            db.session.add(product)

            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                product_name=product.name,
                quantity=item['quantity'],
                unit_price=product.price,
                total_price=product.price * item['quantity'],
                status=1
            )
            update_timestamps(sale_item)
            total_amount += sale_item.total_price
            db.session.add(sale_item)

        sale.total_amount = total_amount

        # Post new GL entries
        txn_id, txn_no_str = generate_transaction_number('SAL')
        entries = [
            {"account_id": 1, "transaction_type": "Debit", "amount": total_amount},   # Cash/Bank
            {"account_id": 2, "transaction_type": "Credit", "amount": total_amount}  # Sales Revenue
        ]
        gl_entries = post_to_ledger(entries, txn_id, description=f"Sale #{sale.id} updated")
        sale.transaction_no = txn_id

    db.session.commit()
    return jsonify({"message": "Sale updated with GL entries", "sale_id": sale.id})


# ------------------ Soft Delete Sale (Status = 0) ------------------ #
@token_required
@sales_bp.route('/<int:sale_id>', methods=['DELETE'])
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    sale.status = 0
    update_timestamps(sale)

    for item in sale.saleitem_set:
        item.status = 0
        update_timestamps(item)
        product = Product.query.get(item.product_id)
        if product:
            product.quantity += item.quantity
            db.session.add(product)

    # Reverse GL entries
    if sale.transaction_no:
        original_entries = GeneralLedger.query.filter_by(transaction_no=sale.transaction_no).all()
        for entry in original_entries:
            reverse_type = 'Credit' if entry.transaction_type == 'Debit' else 'Debit'
            reverse_entry = GeneralLedger(
                account_id=entry.account_id,
                transaction_type=reverse_type,
                amount=entry.amount,
                description=f"Reversal of {entry.description}",
                transaction_date=datetime.utcnow(),
                transaction_no=entry.transaction_no
            )
            db.session.add(reverse_entry)

    db.session.commit()
    return jsonify({"message": "Sale soft deleted and GL reversed", "sale_id": sale_id})




# ------------------ Get Returnable Products Not Fully Returned ------------------ #
@token_required
@sales_bp.route('/returnable/unreturned/new', methods=['GET'])
def get_unreturned_returnables_new():
    """
    Returns a list of returnable product units (bottles/crates) that
    were issued but not fully returned by customers.
    Includes container, bottle, and customer details.
    """
    result = []

    # --- Bottle Transactions ---
    bottle_txns = BottleTransaction.query.filter(
        BottleTransaction.transaction_type.in_(['Issued', 'Returned']),
        BottleTransaction.status == 1
    ).all()

    bottle_summary = {}
    for txn in bottle_txns:
        customer_id = txn.customer.id if txn.customer else 0
        key = (customer_id, txn.product_unit.id, txn.container.id)

        if key not in bottle_summary:
            bottle_summary[key] = {
                "customer_id": customer_id,
                "customer_name": txn.customer.name if txn.customer else "Walk-in",
                "customer_phone": txn.customer.phone if txn.customer else "",
                "customer_email": txn.customer.email if txn.customer else "",
                "customer_address": txn.customer.address if txn.customer else "",
                "unit_type": "Bottle",
                "unit_name": txn.product_unit.unit_name,
                "container_name": txn.container.name,
                "quantity_issued": 0,
                "quantity_returned": 0
            }

        if txn.transaction_type == 'Issued':
            bottle_summary[key]["quantity_issued"] += txn.quantity
        elif txn.transaction_type == 'Returned':
            bottle_summary[key]["quantity_returned"] += txn.quantity

    # --- Container Transactions ---
    container_txns = ContainerTransaction.query.filter(
        ContainerTransaction.transaction_type.in_(['Issued', 'Returned']),
        ContainerTransaction.status == 1
    ).all()

    container_summary = {}
    for txn in container_txns:
        customer_id = txn.customer.id if txn.customer else 0
        key = (customer_id, txn.container.id)

        if key not in container_summary:
            container_summary[key] = {
                "customer_id": customer_id,
                "customer_name": txn.customer.name if txn.customer else "Walk-in",
                "customer_phone": txn.customer.phone if txn.customer else "",
                "customer_email": txn.customer.email if txn.customer else "",
                "customer_address": txn.customer.address if txn.customer else "",
                "unit_type": "Container",
                "unit_name": txn.container.product_unit.unit_name,
                "container_name": txn.container.name,
                "quantity_issued": 0,
                "quantity_returned": 0
            }

        if txn.transaction_type == 'Issued':
            container_summary[key]["quantity_issued"] += txn.quantity
        elif txn.transaction_type == 'Returned':
            container_summary[key]["quantity_returned"] += txn.quantity

    # --- Merge results ---
    for summary in list(bottle_summary.values()) + list(container_summary.values()):
        not_returned = summary["quantity_issued"] - summary["quantity_returned"]
        if not_returned > 0:
            summary["quantity_not_returned"] = not_returned
            result.append(summary)

    return jsonify(result)



# ------------------ Get Returnable Products Not Fully Returned (Optimized) ------------------ #
@token_required
@sales_bp.route('/returnable/unreturned', methods=['GET'])
def get_unreturned_returnables():
    """
    Returns a list of returnable products (bottles/crates) grouped by customer and product,
    showing issued, returned, and not returned quantities. Includes customer and container details.
    """
    result = []

    # --- Bottle Transactions ---
    bottle_txns = BottleTransaction.query.filter(
        BottleTransaction.transaction_type.in_(['Issued', 'Returned']),
        BottleTransaction.status == 1
    ).all()

    # --- Container Transactions ---
    container_txns = ContainerTransaction.query.filter(
        ContainerTransaction.transaction_type.in_(['Issued', 'Returned']),
        ContainerTransaction.status == 1
    ).all()

    # --- Aggregate per customer and product ---
    summary = {}
    for txn in bottle_txns + container_txns:
        customer = txn.customer
        container = txn.container
        product_unit = txn.product_unit if hasattr(txn, 'product_unit') else txn.container.product_unit

        customer_id = customer.id if customer else 0
        product_id = product_unit.product_id

        # Key: customer_id + product_id + container_id
        key = (customer_id, product_id, container.id)

        if key not in summary:
            summary[key] = {
                "customer_id": customer_id,
                "customer_name": customer.name if customer else "Walk-in",
                "customer_phone": customer.phone if customer else "",
                "customer_email": customer.email if customer else "",
                "customer_address": customer.address if customer else "",
                "product_name": product_unit.product.name,
                "unit_names": [],
                "container_names": [],
                "quantity_issued": 0,
                "quantity_returned": 0
            }

        # Track unit and container names
        if txn.__class__.__name__ == "BottleTransaction":
            if product_unit.unit_name not in summary[key]["unit_names"]:
                summary[key]["unit_names"].append(product_unit.unit_name)
        else:
            if product_unit.unit_name not in summary[key]["unit_names"]:
                summary[key]["unit_names"].append(product_unit.unit_name)
            if container.name not in summary[key]["container_names"]:
                summary[key]["container_names"].append(container.name)

        # Count issued and returned
        if txn.transaction_type == 'Issued':
            summary[key]["quantity_issued"] += txn.quantity
        elif txn.transaction_type == 'Returned':
            summary[key]["quantity_returned"] += txn.quantity

    # --- Prepare final result ---
    for s in summary.values():
        not_returned = s["quantity_issued"] - s["quantity_returned"]
        if not_returned > 0:
            result.append({
                "customer_id": s["customer_id"],
                "customer_name": s["customer_name"],
                "customer_phone": s["customer_phone"],
                "customer_email": s["customer_email"],
                "customer_address": s["customer_address"],
                "product_name": s["product_name"],
                "unit_names": s["unit_names"],          # all units (bottles/containers) for this product
                "container_names": s["container_names"], # all container names
                "quantity_issued": s["quantity_issued"],
                "quantity_returned": s["quantity_returned"],
                "quantity_not_returned": not_returned
            })

    return jsonify(result)



# ------------------ Get Returnable Products Not Fully Returned ------------------ #
@token_required
@sales_bp.route('/returnable/unreturned/nn', methods=['GET'])
def get_unreturned_returnables_():
    """
    Returns a list of returnable products (bottles and crates) grouped by customer and product,
    showing quantities issued, returned, and not yet returned.
    """
    result = []

    # --- Query all active bottle and container transactions ---
    bottle_txns = BottleTransaction.query.filter(
        BottleTransaction.transaction_type.in_(['Issued', 'Returned']),
        BottleTransaction.status == 1
    ).all()

    container_txns = ContainerTransaction.query.filter(
        ContainerTransaction.transaction_type.in_(['Issued', 'Returned']),
        ContainerTransaction.status == 1
    ).all()

    # --- Aggregate per customer and product ---
    summary = {}
    for txn in bottle_txns + container_txns:
        customer = txn.customer
        container = txn.container
        product_unit = getattr(txn, 'product_unit', None) or txn.container.product_unit

        customer_id = customer.id if customer else 0
        product_id = product_unit.product_id

        # Use key: (customer_id, product_id, container_id) to group together
        key = (customer_id, product_id, container.id)

        if key not in summary:
            summary[key] = {
                "customer_id": customer_id,
                "customer_name": customer.name if customer else "Walk-in",
                "customer_phone": customer.phone if customer else "",
                "customer_email": customer.email if customer else "",
                "customer_address": customer.address if customer else "",
                "product_name": product_unit.product.name,
                "unit_names": [],
                "container_names": [],
                "quantity_issued": 0,
                "quantity_returned": 0
            }

        # Track unit and container names
        if product_unit.unit_name not in summary[key]["unit_names"]:
            summary[key]["unit_names"].append(product_unit.unit_name)
        if container.name not in summary[key]["container_names"]:
            summary[key]["container_names"].append(container.name)

        # Count quantities based on transaction type
        if txn.transaction_type == 'Issued':
            summary[key]["quantity_issued"] += txn.quantity
        elif txn.transaction_type == 'Returned':
            summary[key]["quantity_returned"] += txn.quantity

    # --- Prepare final result ---
    for s in summary.values():
        quantity_not_returned = s["quantity_issued"] - s["quantity_returned"]
        if quantity_not_returned > 0:
            result.append({
                "customer_id": s["customer_id"],
                "customer_name": s["customer_name"],
                "customer_phone": s["customer_phone"],
                "customer_email": s["customer_email"],
                "customer_address": s["customer_address"],
                "product_name": s["product_name"],
                "unit_names": s["unit_names"],
                "container_names": s["container_names"],
                "quantity_issued": s["quantity_issued"],
                "quantity_returned": s["quantity_returned"],
                "quantity_not_returned": quantity_not_returned
            })

    return jsonify(result)





# ------------------ Get Returnable Products Not Fully Returned (Merged) ------------------ #
@token_required
@sales_bp.route('/returnable/unreturned/merged', methods=['GET'])
def get_unreturned_returnables_merged():
    """
    Returns a list of returnable products (bottles and crates) fully merged per customer and product,
    showing all unit names, container names, quantities issued, returned, and not yet returned.
    """
    result = []

    # --- Query all active bottle and container transactions ---
    bottle_txns = BottleTransaction.query.filter(
        BottleTransaction.transaction_type.in_(['Issued', 'Returned']),
        BottleTransaction.status == 1
    ).all()

    container_txns = ContainerTransaction.query.filter(
        ContainerTransaction.transaction_type.in_(['Issued', 'Returned']),
        ContainerTransaction.status == 1
    ).all()

    # --- Aggregate per customer and product only ---
    summary = {}
    for txn in bottle_txns + container_txns:
        customer = txn.customer
        container = txn.container
        product_unit = getattr(txn, 'product_unit', None) or txn.container.product_unit
        product_id = product_unit.product_id
        customer_id = customer.id if customer else 0

        # Key: (customer_id, product_id) -> merge all containers and units under same product
        key = (customer_id, product_id)

        if key not in summary:
            summary[key] = {
                "customer_id": customer_id,
                "customer_name": customer.name if customer else "Walk-in",
                "customer_phone": customer.phone if customer else "",
                "customer_email": customer.email if customer else "",
                "customer_address": customer.address if customer else "",
                "product_name": product_unit.product.name,
                "unit_names": set(),
                "container_names": set(),
                "quantity_issued": 0,
                "quantity_returned": 0
            }

        summary[key]["unit_names"].add(product_unit.unit_name)
        summary[key]["container_names"].add(container.name)

        if txn.transaction_type == 'Issued':
            summary[key]["quantity_issued"] += txn.quantity
        elif txn.transaction_type == 'Returned':
            summary[key]["quantity_returned"] += txn.quantity

    # --- Prepare final result ---
    for s in summary.values():
        quantity_not_returned = s["quantity_issued"] - s["quantity_returned"]
        if quantity_not_returned > 0:
            result.append({
                "customer_id": s["customer_id"],
                "customer_name": s["customer_name"],
                "customer_phone": s["customer_phone"],
                "customer_email": s["customer_email"],
                "customer_address": s["customer_address"],
                "product_name": s["product_name"],
                "unit_names": list(s["unit_names"]),
                "container_names": list(s["container_names"]),
                "quantity_issued": s["quantity_issued"],
                "quantity_returned": s["quantity_returned"],
                "quantity_not_returned": quantity_not_returned
            })

    return jsonify(result)

@token_required
@sales_bp.route('/returnable/summary/by-customer', methods=['GET'])
def get_customer_returnable_summary():
    """
    Returns both:
    - Crates (Issued & Returned)
    - Bottles (Issued but Not Returned)
    per customer, per product.

    Combines BottleTransaction and ContainerTransaction.
    """
    result = []

    # --- Helper to resolve customer ---
    def resolve_customer(txn):
        if txn.customer:
            return txn.customer
        elif getattr(txn, "sale_id", None):
            sale = Sale.query.get(txn.sale_id)
            if sale and sale.customer:
                return sale.customer
        return None

    # --- 1️⃣ Fetch Crate Transactions ---
    crate_txns = ContainerTransaction.query.filter(
        ContainerTransaction.transaction_type.in_(['Issued', 'Returned','Sold']),
        ContainerTransaction.status == 1
    ).all()

    crate_summary = {}

    for txn in crate_txns:
        customer = resolve_customer(txn)
        if not customer:
            continue

        container = txn.container
        product_unit = getattr(container, 'product_unit', None)
        product = product_unit.product if product_unit else None
        if not product:
            continue

        key = (customer.id, container.id)
        if key not in crate_summary:
            category = db.session.query(Category).filter_by(id=product.category_id, status=1).first()
            crate_summary[key] = {
                "type": "Crate",
                "customer_id": customer.id,
                "customer_name": customer.name,
                "product_name": product.name,
                "category_name":category.name,
                "container_name": container.name,
                "quantity_issued": 0,
                "quantity_returned": 0,
                "quantity_sold":0
            }

        if txn.transaction_type == 'Issued':
            crate_summary[key]["quantity_issued"] += txn.quantity
        elif txn.transaction_type == 'Returned':
            crate_summary[key]["quantity_returned"] += txn.quantity
        elif txn.transaction_type == 'Sold':
            crate_summary[key]["quantity_sold"] += txn.quantity



    # --- 2️⃣ Fetch Bottle Transactions (only show those not fully returned) ---
    bottle_txns = BottleTransaction.query.filter(
        BottleTransaction.transaction_type.in_(['Issued', 'Returned','Sold']),
        BottleTransaction.status == 1
    ).all()

    bottle_summary = {}

    for txn in bottle_txns:
        customer = resolve_customer(txn)
        if not customer:
            continue

        container = txn.container
        product_unit = txn.product_unit
        product = product_unit.product if product_unit else None
        if not product:
            continue

        key = (customer.id, product_unit.id)
        if key not in bottle_summary:
            category = db.session.query(Category).filter_by(id=product.category_id, status=1).first()

            bottle_summary[key] = {
                "type": "Bottle",
                "customer_id": customer.id,
                "customer_name": customer.name,
                "product_name": product.name,
                "category_name":category.name,

                "unit_name": product_unit.unit_name,

                "container_name": container.name if container else None,
                "quantity_issued": 0,
                "quantity_returned": 0,
                "quantity_sold":0

            }

        if txn.transaction_type == 'Issued':
            bottle_summary[key]["quantity_issued"] += txn.quantity
        elif txn.transaction_type == 'Returned':
            bottle_summary[key]["quantity_returned"] += txn.quantity
        elif txn.transaction_type == 'Sold':
            bottle_summary[key]["quantity_sold"] += txn.quantity

    # --- 3️⃣ Prepare result list ---
    # Crates: Always show both issued & returned
    for s in crate_summary.values():
        s["quantity_not_returned"] = s["quantity_issued"] - s["quantity_returned"] -s["quantity_sold"]
        result.append(s)

    # Bottles: Only show where not all returned
    for s in bottle_summary.values():
        not_returned = s["quantity_issued"] - s["quantity_returned"] -s["quantity_sold"]
        if not_returned > 0:
            s["quantity_not_returned"] = not_returned
            result.append(s)

    # Sort by customer then product
    result.sort(key=lambda x: (x["customer_name"], x["type"], x["product_name"]))

    return jsonify(result), 200


@token_required
@sales_bp.route('/returnable/summary/customer/<int:customer_id>', methods=['GET'])
def get_returnable_summary_for_customer(customer_id):
    """
    Returns both:
    - Crates (Issued, Returned, Sold)
    - Bottles (Issued, Returned, Sold)
    for a specific customer, per product.
    """
    result = []

    # --- Helper to resolve customer ---
    def resolve_customer(txn):
        if txn.customer:
            return txn.customer
        elif getattr(txn, "sale_id", None):
            sale = Sale.query.get(txn.sale_id)
            if sale and sale.customer:
                return sale.customer
        return None

    # --- 1️⃣ Fetch Crate Transactions ---
    crate_txns = ContainerTransaction.query.filter(
        ContainerTransaction.transaction_type.in_(['Issued', 'Returned', 'Sold']),
        ContainerTransaction.status == 1
    ).all()

    crate_summary = {}

    for txn in crate_txns:
        customer = resolve_customer(txn)
        if not customer or customer.id != customer_id:
            continue

        container = txn.container
        product_unit = getattr(container, 'product_unit', None)
        product = product_unit.product if product_unit else None
        if not product:
            continue

        key = (customer.id, container.id)
        if key not in crate_summary:
            crate_summary[key] = {
                "type": "Crate",
                "customer_id": customer.id,
                "customer_name": customer.name,
                "product_name": product.name,
                "container_name": container.name,
                "quantity_issued": 0,
                "quantity_returned": 0,
                "quantity_sold": 0
            }

        if txn.transaction_type == 'Issued':
            crate_summary[key]["quantity_issued"] += txn.quantity
        elif txn.transaction_type == 'Returned':
            crate_summary[key]["quantity_returned"] += txn.quantity
        elif txn.transaction_type == 'Sold':
            crate_summary[key]["quantity_sold"] += txn.quantity

    # --- 2️⃣ Fetch Bottle Transactions ---
    bottle_txns = BottleTransaction.query.filter(
        BottleTransaction.transaction_type.in_(['Issued', 'Returned', 'Sold']),
        BottleTransaction.status == 1
    ).all()

    bottle_summary = {}

    for txn in bottle_txns:
        customer = resolve_customer(txn)
        if not customer or customer.id != customer_id:
            continue

        container = txn.container
        product_unit = txn.product_unit
        product = product_unit.product if product_unit else None
        if not product:
            continue

        key = (customer.id, product_unit.id)
        if key not in bottle_summary:
            bottle_summary[key] = {
                "type": "Bottle",
                "customer_id": customer.id,
                "customer_name": customer.name,
                "product_name": product.name,
                "unit_name": product_unit.unit_name,
                "container_name": container.name if container else None,
                "quantity_issued": 0,
                "quantity_returned": 0,
                "quantity_sold": 0
            }

        if txn.transaction_type == 'Issued':
            bottle_summary[key]["quantity_issued"] += txn.quantity
        elif txn.transaction_type == 'Returned':
            bottle_summary[key]["quantity_returned"] += txn.quantity
        elif txn.transaction_type == 'Sold':
            bottle_summary[key]["quantity_sold"] += txn.quantity

    # --- 3️⃣ Prepare result list ---
    # Crates: Always show both issued & returned
    for s in crate_summary.values():
        s["quantity_not_returned"] = s["quantity_issued"] - s["quantity_returned"] - s["quantity_sold"]
        if s["quantity_not_returned"] > 0:
            result.append(s)

    # Bottles: Only show where not all returned
    for s in bottle_summary.values():
        not_returned = s["quantity_issued"] - s["quantity_returned"] - s["quantity_sold"]
        if not_returned > 0:
            s["quantity_not_returned"] = not_returned
            result.append(s)

    # --- Sort neatly ---
    result.sort(key=lambda x: (x["type"], x["product_name"]))

    return jsonify(result), 200


# @token_required
# @sales_bp.route('/returnable/summary/customer/<int:customer_id>', methods=['GET'])
# def get_returnable_summary_for_customer(customer_id):
#     """
#     Returns both:
#     - Crates (Issued & Returned)
#     - Bottles (Issued but Not Returned)
#     for a specific customer, per product.
#     """
#     result = []

#     # --- Helper to resolve customer ---
#     def resolve_customer(txn):
#         if txn.customer:
#             return txn.customer
#         elif getattr(txn, "sale_id", None):
#             sale = Sale.query.get(txn.sale_id)
#             if sale and sale.customer:
#                 return sale.customer
#         return None

#     # --- 1️⃣ Fetch Crate Transactions ---
#     crate_txns = ContainerTransaction.query.filter(
#         ContainerTransaction.transaction_type.in_(['Issued', 'Returned']),
#         ContainerTransaction.status == 1
#     ).all()

#     crate_summary = {}

#     for txn in crate_txns:
#         customer = resolve_customer(txn)
#         if not customer or customer.id != customer_id:
#             continue

#         container = txn.container
#         product_unit = getattr(container, 'product_unit', None)
#         product = product_unit.product if product_unit else None
#         if not product:
#             continue

#         key = (customer.id, container.id)
#         if key not in crate_summary:
#             crate_summary[key] = {
#                 "type": "Crate",
#                 "customer_id": customer.id,
#                 "customer_name": customer.name,
#                 "product_name": product.name,
#                 "container_name": container.name,
#                 "quantity_issued": 0,
#                 "quantity_returned": 0,
#                 # "quantity_sold":0
#             }

#         if txn.transaction_type == 'Issued':
#             crate_summary[key]["quantity_issued"] += txn.quantity
#         elif txn.transaction_type == 'Returned':
#             crate_summary[key]["quantity_returned"] += txn.quantity
#         # elif txn.transaction_type == 'Sold':
#         #     crate_summary[key]["quantity_sold"] += txn.quantity

#     # --- 2️⃣ Fetch Bottle Transactions (only show those not fully returned) ---
#     bottle_txns = BottleTransaction.query.filter(
#         BottleTransaction.transaction_type.in_(['Issued', 'Returned']),
#         BottleTransaction.status == 1
#     ).all()

#     bottle_summary = {}

#     for txn in bottle_txns:
#         customer = resolve_customer(txn)
#         if not customer or customer.id != customer_id:
#             continue

#         container = txn.container
#         product_unit = txn.product_unit
#         product = product_unit.product if product_unit else None
#         if not product:
#             continue

#         key = (customer.id, product_unit.id)
#         if key not in bottle_summary:
#             bottle_summary[key] = {
#                 "type": "Bottle",
#                 "customer_id": customer.id,
#                 "customer_name": customer.name,
#                 "product_name": product.name,
#                 "unit_name": product_unit.unit_name,
#                 "container_name": container.name if container else None,
#                 "quantity_issued": 0,
#                 "quantity_returned": 0,
#                 # "quantity_sold":0

#             }

#         if txn.transaction_type == 'Issued':
#             bottle_summary[key]["quantity_issued"] += txn.quantity
#         elif txn.transaction_type == 'Returned':
#             bottle_summary[key]["quantity_returned"] += txn.quantity
#         # elif txn.transaction_type == 'Sold':
#         #     bottle_summary[key]["quantity_sold"] += txn.quantity

#     # --- 3️⃣ Prepare result list ---
#     for s in crate_summary.values():
#         s["quantity_not_returned"] = s["quantity_issued"] - s["quantity_returned"]

#     for s in bottle_summary.values():
#         not_returned = s["quantity_issued"] - s["quantity_returned"]
#         if not_returned > 0:
#             s["quantity_not_returned"] = not_returned
#             result.append(s)

#     # Sort by type then product
#     result.sort(key=lambda x: (x["type"], x["product_name"]))

#     return jsonify(result), 200



@token_required
@sales_bp.route('/returnable/return', methods=['POST'])
def record_returnable_returns():
    """
    Record crate and/or bottle returns from a customer (based on sale_id).
    Handles full or partial returns, including damaged bottles and crates.
    """
    data = request.json
    sale_id = data.get('sale_id')
    returned_items = data.get('items', [])

    if not sale_id:
        return jsonify({"error": "sale_id is required"}), 400
    if not returned_items:
        return jsonify({"error": "No return items provided"}), 400

    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"error": f"Sale ID {sale_id} not found"}), 404

    customer = sale.customer
    if not customer:
        return jsonify({"error": "Sale has no associated customer"}), 400

    try:
        for item in returned_items:
            product_unit_id = item.get("product_unit_id")
            container_id = item.get("container_id")
            bottles_returned = item.get("bottles_returned", 0)
            bottles_damaged = item.get("bottles_damaged", 0)
            crates_returned = item.get("crates_returned", 0)
            crates_damaged = item.get("crates_damaged", 0)

            # --- 1️⃣ Handle Crate Returns ---
            if container_id and crates_returned > 0:
                container = ReturnableContainer.query.get(container_id)
                if not container:
                    continue

                crate_return_txn = ContainerTransaction(
                    container_id=container.id,
                    sale_id=sale_id,
                    customer_id=customer.id,
                    transaction_type="Returned",
                    quantity=crates_returned,
                    timestamp=datetime.utcnow(),
                    status=1
                )
                db.session.add(crate_return_txn)

                container.total_returned += crates_returned
                # container.total_in_stock += crates_returned

            # --- 2️⃣ Handle Crate Damages ---
            if container_id and crates_damaged > 0:
                container = ReturnableContainer.query.get(container_id)
                if not container:
                    continue

                crate_damage_txn = ContainerTransaction(
                    container_id=container.id,
                    sale_id=sale_id,
                    customer_id=customer.id,
                    transaction_type="Damaged",
                    quantity=crates_damaged,
                    timestamp=datetime.utcnow(),
                    status=1
                )
                db.session.add(crate_damage_txn)

                container.total_damaged += crates_damaged
                # container.total_in_stock +=crates_damaged

            # --- 3️⃣ Handle Bottle Returns ---
            if product_unit_id and bottles_returned > 0:
                product_unit = ProductUnit.query.get(product_unit_id)
                if not product_unit:
                    continue

                bottle_return_txn = BottleTransaction(
                    container_id=container_id,
                    product_unit_id=product_unit_id,
                    sale_id=sale_id,
                    customer_id=customer.id,
                    transaction_type="Returned",
                    quantity=bottles_returned,
                    unit_value=product_unit.cost_price or 0,
                    timestamp=datetime.utcnow(),
                    status=1
                )
                bottle_return_txn.calculate_total_value()
                db.session.add(bottle_return_txn)

            # --- 4️⃣ Handle Bottle Damages ---
            if product_unit_id and bottles_damaged > 0:
                product_unit = ProductUnit.query.get(product_unit_id)
                if not product_unit:
                    continue

                bottle_damage_txn = BottleTransaction(
                    container_id=container_id,
                    product_unit_id=product_unit_id,
                    sale_id=sale_id,
                    customer_id=customer.id,
                    transaction_type="Damaged",
                    quantity=bottles_damaged,
                    unit_value=product_unit.cost_price or 0,
                    timestamp=datetime.utcnow(),
                    status=1
                )
                bottle_damage_txn.calculate_total_value()
                db.session.add(bottle_damage_txn)

        db.session.commit()

        return jsonify({
            "message": "Returnable items successfully recorded",
            "sale_id": sale_id,
            "customer_name": customer.name,
            "items_recorded": len(returned_items)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500



@token_required
@sales_bp.route('/returnable/pending-sales', methods=['GET'])
def get_sales_with_pending_returns():
    """
    Returns all sales where customers still have returnable items (crates/bottles)
    that have not been fully returned. Includes customer and product details.
    """
    try:
        result = []

        # --- Fetch all active sales ---
        sales = Sale.query.filter(Sale.status.in_([1, 2, 3, 4])).order_by(Sale.id.desc()).all()

        for s in sales:
            customer = s.customer
            if not customer:
                continue  # skip sales without customer

            pending_items = []

            # --- Check Bottle Transactions ---
            bottle_txns = BottleTransaction.query.filter(
                BottleTransaction.sale_id == s.id,
                BottleTransaction.status == 1,
                BottleTransaction.transaction_type.in_(["Issued", "Returned"])
            ).all()

            # Aggregate by product unit
            bottle_summary = {}
            for txn in bottle_txns:
                unit_id = txn.product_unit_id
                if unit_id not in bottle_summary:
                    bottle_summary[unit_id] = {"issued": 0, "returned": 0, "product_unit": txn.product_unit, "container": txn.container}

                if txn.transaction_type == "Issued":
                    bottle_summary[unit_id]["issued"] += txn.quantity
                elif txn.transaction_type == "Returned":
                    bottle_summary[unit_id]["returned"] += txn.quantity

            # Only include bottles with pending quantity
            for summary in bottle_summary.values():
                not_returned = summary["issued"] - summary["returned"]
                if not_returned > 0:
                    pending_items.append({
                        "type": "Bottle",
                        "product_unit_id": summary["product_unit"].id,
                        "product_name": summary["product_unit"].product.name,
                        "unit_name": summary["product_unit"].unit_name,
                        "container_id": summary["container"].id if summary["container"] else None,
                        "container_name": summary["container"].name if summary["container"] else None,
                        "quantity_issued": summary["issued"],
                        "quantity_returned": summary["returned"],
                        "quantity_not_returned": not_returned
                    })

            # --- Check Crate Transactions ---
            crate_txns = ContainerTransaction.query.filter(
                ContainerTransaction.sale_id == s.id,
                ContainerTransaction.status == 1,
                ContainerTransaction.transaction_type.in_(["Issued", "Returned"])
            ).all()

            crate_summary = {}
            for txn in crate_txns:
                container_id = txn.container_id
                if container_id not in crate_summary:
                    crate_summary[container_id] = {"issued": 0, "returned": 0, "container": txn.container}

                if txn.transaction_type == "Issued":
                    crate_summary[container_id]["issued"] += txn.quantity
                elif txn.transaction_type == "Returned":
                    crate_summary[container_id]["returned"] += txn.quantity

            # Only include crates with pending quantity
            for summary in crate_summary.values():
                not_returned = summary["issued"] - summary["returned"]
                if not_returned > 0:
                    pending_items.append({
                        "type": "Crate",
                        "container_id": summary["container"].id,
                        "container_name": summary["container"].name,
                        "product_name": summary["container"].product_unit.product.name,
                        "unit_name": summary["container"].product_unit.unit_name,
                        "quantity_issued": summary["issued"],
                        "quantity_returned": summary["returned"],
                        "quantity_not_returned": not_returned
                    })

            # Only include sales that have pending items
            if pending_items:
                result.append({
                    "sale_id": s.id,
                    "sale_number": s.sale_number,
                    "customer": {
                        "id": customer.id,
                        "name": customer.name,
                        "mobile": getattr(customer, "mobile", ""),
                        "email": getattr(customer, "email", ""),
                        "address": getattr(customer, "address", "")
                    },
                    "pending_items": pending_items
                })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500




def get_pending_bottles_for_sale(sale_id):
    """
    Helper to get number of bottles still pending return for a sale.
    """
    total_sold = (
        db.session.query(db.func.sum(BottleTransaction.quantity))
        .filter(BottleTransaction.sale_id == sale_id,
                BottleTransaction.transaction_type == "Issued")
        .scalar() or 0
    )
    total_returned = (
        db.session.query(db.func.sum(BottleTransaction.quantity))
        .filter(BottleTransaction.sale_id == sale_id,
                BottleTransaction.transaction_type == "Returned")
        .scalar() or 0
    )
    return max(total_sold - total_returned, 0)


def get_pending_crates_for_sale(sale_id):
    """
    Helper to get number of crates still pending return for a sale.
    """
    total_sold = (
        db.session.query(db.func.sum(ContainerTransaction.quantity))
        .filter(ContainerTransaction.sale_id == sale_id,
                ContainerTransaction.transaction_type == "Issued")
        .scalar() or 0
    )
    total_returned = (
        db.session.query(db.func.sum(ContainerTransaction.quantity))
        .filter(ContainerTransaction.sale_id == sale_id,
                ContainerTransaction.transaction_type == "Returned")
        .scalar() or 0
    )
    return max(total_sold - total_returned, 0)


# @token_required
# @sales_bp.route('/returnable/auto_return', methods=['POST'])
# def auto_returnable_for_customer():
#     """
#     Automatically apply returned and damaged crates/bottles for a customer
#     across all sales with pending returnables (FIFO).
#     User provides:
#       - customer_id
#       - bottles_returned
#       - crates_returned
#       - bottles_damaged (optional)
#       - crates_damaged (optional)
#     """
#     data = request.json
#     customer_id = data.get("customer_id")

#     bottles_returned = data.get("bottles_returned", 0)
#     crates_returned = data.get("crates_returned", 0)
#     bottles_damaged = data.get("bottles_damaged", 0)
#     crates_damaged = data.get("crates_damaged", 0)

#     if not customer_id:
#         return jsonify({"error": "customer_id is required"}), 400

#     if all(x <= 0 for x in [bottles_returned, crates_returned, bottles_damaged, crates_damaged]):
#         return jsonify({"error": "At least one of the return/damage quantities must be > 0"}), 400

#     customer = Customer.query.get(customer_id)
#     if not customer:
#         return jsonify({"error": f"Customer ID {customer_id} not found"}), 404

#     try:
#         # Step 1️⃣: Get all sales for this customer with pending returnables
#         pending_sales = (
#             db.session.query(Sale)
#             .filter(Sale.customer_id == customer_id, Sale.status == 1)
#             .order_by(Sale.sale_date.asc())
#             .all()
#         )

#         if not pending_sales:
#             return jsonify({"message": "No pending sales for this customer"}), 200

#         total_bottles_applied = 0
#         total_crates_applied = 0
#         total_bottles_damaged_applied = 0
#         total_crates_damaged_applied = 0

#         # Step 2️⃣: Apply returns/damages FIFO across pending sales
#         for sale in pending_sales:
#             applied_bottles, applied_crates, applied_bottles_damaged, applied_crates_damaged = apply_return_for_sale(
#                 sale,
#                 customer,
#                 bottles_to_return=bottles_returned,
#                 crates_to_return=crates_returned,
#                 bottles_damaged=bottles_damaged,
#                 crates_damaged=crates_damaged
#             )

#             total_bottles_applied += applied_bottles
#             total_crates_applied += applied_crates
#             total_bottles_damaged_applied += applied_bottles_damaged
#             total_crates_damaged_applied += applied_crates_damaged

#             # Reduce remaining quantities to allocate to next sales
#             bottles_returned -= applied_bottles
#             crates_returned -= applied_crates
#             bottles_damaged -= applied_bottles_damaged
#             crates_damaged -= applied_crates_damaged

#             # Stop if all quantities have been allocated
#             if all(x <= 0 for x in [bottles_returned, crates_returned, bottles_damaged, crates_damaged]):
#                 break

#         db.session.commit()

#         return jsonify({
#             "message": "Returnable items automatically applied successfully",
#             "customer_name": customer.name,
#             "total_crates_applied": total_crates_applied,
#             "total_bottles_applied": total_bottles_applied,
#             "total_crates_damaged_applied": total_crates_damaged_applied,
#             "total_bottles_damaged_applied": total_bottles_damaged_applied
#         }), 201

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# @token_required
# @sales_bp.route('/returnable/auto_return', methods=['POST'])
# def auto_returnable_for_customer():
#     """
#     Automatically apply returned and damaged crates/bottles for a customer
#     across all sales with pending returnables (FIFO).
#     User provides:
#       - customer_id
#       - items: [
#             {
#                 product_unit_id (optional),
#                 container_id (optional),
#                 bottles_returned,
#                 crates_returned,
#                 bottles_damaged,
#                 crates_damaged
#             },
#             ...
#         ]
#     """
#     data = request.json
#     customer_id = data.get("customer_id")
#     items = data.get("items", [])

#     if not customer_id:
#         return jsonify({"error": "customer_id is required"}), 400

#     if not items or all(
#         all(x <= 0 for x in [
#             item.get("bottles_returned", 0),
#             item.get("crates_returned", 0),
#             item.get("bottles_damaged", 0),
#             item.get("crates_damaged", 0)
#         ]) for item in items
#     ):
#         return jsonify({"error": "At least one of the return/damage quantities must be > 0"}), 400

#     customer = Customer.query.get(customer_id)
#     if not customer:
#         return jsonify({"error": f"Customer ID {customer_id} not found"}), 404

#     try:
#         # Step 1️⃣: Get all sales for this customer with pending returnables
#         pending_sales = (
#             db.session.query(Sale)
#             .filter(Sale.customer_id == customer_id, Sale.status.in_([1, 2, 3, 4] ))
#             .order_by(Sale.sale_date.asc())
#             .all()
#         )

#         if not pending_sales:
#             return jsonify({"message": "No pending sales for this customer"}), 200

#         total_bottles_applied = 0
#         total_crates_applied = 0
#         total_bottles_damaged_applied = 0
#         total_crates_damaged_applied = 0

#         # Step 2️⃣: Apply returns/damages FIFO for each item
#         for item in items:
#             bottles_returned = item.get("bottles_returned", 0)
#             crates_returned = item.get("crates_returned", 0)
#             bottles_damaged = item.get("bottles_damaged", 0)
#             crates_damaged = item.get("crates_damaged", 0)
#             product_unit_id = item.get("product_unit_id")
#             container_id = item.get("container_id")

#             if all(x <= 0 for x in [bottles_returned, crates_returned, bottles_damaged, crates_damaged]):
#                 continue  # skip this item

#             # Apply FIFO logic per sale
#             for sale in pending_sales:
#                 applied_bottles, applied_crates, applied_bottles_damaged, applied_crates_damaged = apply_return_for_sale(
#                     sale,
#                     customer,
#                     # product_unit_id=product_unit_id,
#                     # container_id=container_id,
#                     bottles_to_return=bottles_returned,
#                     crates_to_return=crates_returned,
#                     bottles_damaged=bottles_damaged,
#                     crates_damaged=crates_damaged
#                 )

#                 total_bottles_applied += applied_bottles
#                 total_crates_applied += applied_crates
#                 total_bottles_damaged_applied += applied_bottles_damaged
#                 total_crates_damaged_applied += applied_crates_damaged

#                 # Reduce remaining quantities to allocate to next sales
#                 bottles_returned -= applied_bottles
#                 crates_returned -= applied_crates
#                 bottles_damaged -= applied_bottles_damaged
#                 crates_damaged -= applied_crates_damaged

#                 # Stop if all quantities have been allocated for this item
#                 if all(x <= 0 for x in [bottles_returned, crates_returned, bottles_damaged, crates_damaged]):
#                     break

#         db.session.commit()

#         return jsonify({
#             "message": "Returnable items automatically applied successfully",
#             "customer_name": customer.name,
#             "total_crates_applied": total_crates_applied,
#             "total_bottles_applied": total_bottles_applied,
#             "total_crates_damaged_applied": total_crates_damaged_applied,
#             "total_bottles_damaged_applied": total_bottles_damaged_applied
#         }), 201

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# def apply_return_for_sale(
#     sale, 
#     customer, 
#     bottles_to_return=0, 
#     crates_to_return=0, 
#     bottles_damaged=0, 
#     crates_damaged=0
# ):
#     """
#     Apply returned and damaged crates/bottles for a single sale.
#     Properly updates Container and ProductUnit stock.
#     Returns applied quantities for each category.
#     """
#     applied_bottles = 0
#     applied_crates = 0
#     applied_bottles_damaged = 0
#     applied_crates_damaged = 0

#     # --- Containers linked to sale's product units ---
#     sale_items = SaleItem.query.filter_by(sale_id=sale.id).all()

#     for item in sale_items:
#         # --- Handle Crates ---
#         containers = ReturnableContainer.query.filter_by(product_unit_id=item.unit_id).all()
#         for container in containers:
#             pending_crates = max(0, container.total_issued - container.total_returned - container.total_damaged)
#             if crates_to_return > 0 and pending_crates > 0:
#                 qty = min(crates_to_return, pending_crates)
#                 txn = ContainerTransaction(
#                     container_id=container.id,
#                     sale_id=sale.id,
#                     customer_id=customer.id,
#                     transaction_type="Returned",
#                     quantity=qty,
#                     timestamp=datetime.utcnow(),
#                     status=1
#                 )
#                 db.session.add(txn)
#                 container.process_transaction('Returned', qty)
#                 applied_crates += qty
#                 crates_to_return -= qty

#             if crates_damaged > 0 and pending_crates > 0:
#                 qty = min(crates_damaged, pending_crates)
#                 txn = ContainerTransaction(
#                     container_id=container.id,
#                     sale_id=sale.id,
#                     customer_id=customer.id,
#                     transaction_type="Damaged",
#                     quantity=qty,
#                     timestamp=datetime.utcnow(),
#                     status=1
#                 )
#                 db.session.add(txn)
#                 container.process_transaction('Damaged', qty)
#                 applied_crates_damaged += qty
#                 crates_damaged -= qty

#         # --- Handle Bottles ---
#         pending_bottles = get_pending_bottles_for_sale(sale.id)
#         if bottles_to_return > 0 and pending_bottles > 0:
#             qty = min(bottles_to_return, pending_bottles)
#             txn = BottleTransaction(
#                 container_id=None,
#                 product_unit_id=item.unit_id,
#                 sale_id=sale.id,
#                 customer_id=customer.id,
#                 transaction_type="Returned",
#                 quantity=qty,
#                 unit_value=item.unit_price,
#                 timestamp=datetime.utcnow(),
#                 status=1
#             )
#             txn.calculate_total_value()
#             db.session.add(txn)
#             applied_bottles += qty
#             bottles_to_return -= qty

#         if bottles_damaged > 0 and pending_bottles > 0:
#             qty = min(bottles_damaged, pending_bottles)
#             txn = BottleTransaction(
#                 container_id=None,
#                 product_unit_id=item.unit_id,
#                 sale_id=sale.id,
#                 customer_id=customer.id,
#                 transaction_type="Damaged",
#                 quantity=qty,
#                 unit_value=item.unit_price,
#                 timestamp=datetime.utcnow(),
#                 status=1
#             )
#             txn.calculate_total_value()
#             db.session.add(txn)
#             applied_bottles_damaged += qty
#             bottles_damaged -= qty

#     return applied_bottles, applied_crates, applied_bottles_damaged, applied_crates_damaged


@token_required
@sales_bp.route('/returnable/auto_return_or_sell', methods=['POST'])
def auto_returnable_or_sell_for_customer():
    """
    Automatically apply returned, damaged, or sold crates/bottles for a customer
    across all sales with pending returnables (FIFO).
    User provides:
      - customer_id
      - items: [
            {
                product_unit_id (optional),
                container_id (optional),
                bottles_returned,
                crates_returned,
                bottles_damaged,
                crates_damaged,
                bottles_sold,
                crates_sold
            },
            ...
        ]
    """
    data = request.json
    customer_id = data.get("customer_id")
    items = data.get("items", [])

    if not customer_id:
        return jsonify({"error": "customer_id is required"}), 400

    if not items or all(
        all(x <= 0 for x in [
            item.get("bottles_returned", 0),
            item.get("crates_returned", 0),
            item.get("bottles_damaged", 0),
            item.get("crates_damaged", 0),
            item.get("bottles_sold", 0),
            item.get("crates_sold", 0),
        ]) for item in items
    ):
        return jsonify({"error": "At least one of the quantities must be > 0"}), 400

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": f"Customer ID {customer_id} not found"}), 404

    # try:
        # Fetch all sales for this customer with pending returnables#peter0304
    pending_sales = (
        db.session.query(Sale)
        .filter(Sale.customer_id == customer_id, Sale.status.in_([1,2,3,4]))
        .order_by(Sale.sale_date.asc())
        .all()
    )

    if not pending_sales:
        return jsonify({"message": "No pending sales for this customer"}), 200

    total_bottles_applied = total_crates_applied = 0
    total_bottles_damaged_applied = total_crates_damaged_applied = 0
    total_bottles_sold = total_crates_sold = 0
    crates_sold_amount=0
    bottles_sold_amount=0


    # Apply returns, damages, and sales
    for item in items:
        quantities = {
            "bottles_returned": item.get("bottles_returned", 0),
            "crates_returned": item.get("crates_returned", 0),
            "bottles_damaged": item.get("bottles_damaged", 0),
            "crates_damaged": item.get("crates_damaged", 0),
            "bottles_sold": item.get("bottles_sold", 0),
            "crates_sold": item.get("crates_sold", 0)
        }
        # product_unit_id = item.get("product_unit_id")
        # container_id = item.get("container_id")
        if item.get("crates_sold") :
            crates_sold_amount+=item.get("crates_sold")*item.get("crates_sold_amount")
        if item.get("bottles_sold"):
            bottles_sold_amount +=item.get("bottles_sold")*item.get("bottles_sold_amount")



        # Apply FIFO per sale
        for sale in pending_sales:
            applied = apply_return_or_sell_for_sale(
                sale,
                customer,
                # product_unit_id=product_unit_id,
                # container_id=container_id,
                **quantities
            )

            # Update totals
            total_bottles_applied += applied["bottles_returned"]
            total_crates_applied += applied["crates_returned"]
            total_bottles_damaged_applied += applied["bottles_damaged"]
            total_crates_damaged_applied += applied["crates_damaged"]
            total_bottles_sold += applied["bottles_sold"]
            total_crates_sold += applied["crates_sold"]

            # Decrease remaining quantities for next sale
            for k in quantities.keys():
                quantities[k] -= applied[k]

            # Stop if all quantities allocated
            if all(v <= 0 for v in quantities.values()):
                break
    if crates_sold_amount > 0 or bottles_sold_amount>0:
        amount = crates_sold_amount+bottles_sold_amount
        # Post new GL entries
        txn_id, txn_no_str = generate_transaction_number('BUY-BOTTLE')
        payment_account_code= Account.query.filter(Account.id==data.get("cash_account_id")).first().code

        entries = [
            {"account_id": payment_account_code, "transaction_type": "Debit", "amount": amount},
            {"account_id": 4010, "transaction_type": "Credit", "amount": amount},
            # {"account_id": 5010, "transaction_type": "Debit", "amount": cogs_total},
            # {"account_id": 1400, "transaction_type": "Credit", "amount": cogs_total},
        ]
        gl_entries = post_to_ledger(entries, transaction_no_id=txn_id, description=f"Crate and Bottle Sale of  #{customer_id}")
        # payment.transaction_no = txn_id



    db.session.commit()

    return jsonify({
        "message": "Returnable items and sales applied successfully",
        "customer_name": customer.name,
        "total_crates_applied": total_crates_applied,
        "total_bottles_applied": total_bottles_applied,
        "total_crates_damaged_applied": total_crates_damaged_applied,
        "total_bottles_damaged_applied": total_bottles_damaged_applied,
        "total_crates_sold": total_crates_sold,
        "total_bottles_sold": total_bottles_sold
    }), 201

    # except Exception as e:
    #     db.session.rollback()
    #     return jsonify({"error": f"Internal server error: {str(e)}"}), 500


def apply_return_or_sell_for_sale(
    sale,
    customer,
    # product_unit_id=None,
    # container_id=None,
    bottles_returned=0,
    crates_returned=0,
    bottles_damaged=0,
    crates_damaged=0,
    bottles_sold=0,
    crates_sold=0
):
    """
    Apply returned, damaged, or sold crates/bottles for a single sale.
    Updates Container and BottleTransaction stock and sold counts.
    """
    applied = {
        "bottles_returned": 0,
        "crates_returned": 0,
        "bottles_damaged": 0,
        "crates_damaged": 0,
        "bottles_sold": 0,
        "crates_sold": 0
    }

    sale_items = SaleItem.query.filter_by(sale_id=sale.id).all()

    for item in sale_items:
        # --- Containers (Crates) ---
        containers = ReturnableContainer.query.filter_by(product_unit_id=item.unit_id).all()
        for container in containers:
            pending_crates = max(0, container.total_issued - container.total_returned - container.total_damaged)
            # Returned
            if crates_returned > 0 and pending_crates > 0:
                qty = min(crates_returned, pending_crates)
                txn = ContainerTransaction(
                    container_id=container.id,
                    sale_id=sale.id,
                    customer_id=customer.id,
                    transaction_type="Returned",
                    quantity=qty,
                    unit_value=container.unit_value,
                    timestamp=datetime.utcnow(),
                    status=1
                )
                db.session.add(txn)
                container.process_transaction("Returned", qty)
                applied["crates_returned"] += qty
                crates_returned -= qty

            # Damaged
            if crates_damaged > 0 and pending_crates > 0:
                qty = min(crates_damaged, pending_crates)
                txn = ContainerTransaction(
                    container_id=container.id,
                    sale_id=sale.id,
                    customer_id=customer.id,
                    transaction_type="Damaged",
                    quantity=qty,
                    unit_value=container.unit_value,
                    timestamp=datetime.utcnow(),
                    status=1
                )
                db.session.add(txn)
                container.process_transaction("Damaged", qty)
                applied["crates_damaged"] += qty
                crates_damaged -= qty

            # Sold
            if crates_sold > 0 and pending_crates > 0:
                qty = min(crates_sold, pending_crates)
                txn = ContainerTransaction(
                    container_id=container.id,
                    sale_id=sale.id,
                    customer_id=customer.id,
                    transaction_type="Sold",
                    quantity=qty,
                    unit_value=container.unit_value,
                    total_value=qty*container.unit_value,
                    timestamp=datetime.utcnow(),
                    status=1,
                    sold_quantity=qty
                )
                db.session.add(txn)
                print(" Quantity  ",qty)
                container.process_transaction("Sold", qty, sold=True)
                applied["crates_sold"] += qty
                crates_sold -= qty

        # --- Bottles ---
        pending_bottles = get_pending_bottles_for_sale(sale.id)
        # Returned
        if bottles_returned > 0 and pending_bottles > 0:
            qty = min(bottles_returned, pending_bottles)
            txn = BottleTransaction(
                container_id=None,
                product_unit_id=item.unit_id,
                sale_id=sale.id,
                customer_id=customer.id,
                transaction_type="Returned",
                quantity=qty,
                unit_value=item.unit_price,
                timestamp=datetime.utcnow(),
                bottles_sold=0
            )
            txn.calculate_total_value()
            db.session.add(txn)
            applied["bottles_returned"] += qty
            bottles_returned -= qty

        # Damaged
        if bottles_damaged > 0 and pending_bottles > 0:
            qty = min(bottles_damaged, pending_bottles)
            txn = BottleTransaction(
                container_id=None,
                product_unit_id=item.unit_id,
                sale_id=sale.id,
                customer_id=customer.id,
                transaction_type="Damaged",
                quantity=qty,
                unit_value=item.unit_price,
                timestamp=datetime.utcnow(),
                bottles_sold=0
            )
            txn.calculate_total_value()
            db.session.add(txn)
            applied["bottles_damaged"] += qty
            bottles_damaged -= qty

        # Sold
        if bottles_sold > 0 and pending_bottles > 0:
            qty = min(bottles_sold, pending_bottles)
            txn = BottleTransaction(
                container_id=None,
                product_unit_id=item.unit_id,
                sale_id=sale.id,
                customer_id=customer.id,
                transaction_type="Sold",
                quantity=qty,
                unit_value=item.unit_price,
                total_value=qty*item.unit_price,
                timestamp=datetime.utcnow(),
                bottles_sold=qty
            )
            txn.calculate_total_value()
            db.session.add(txn)
            applied["bottles_sold"] += qty
            bottles_sold -= qty

    return applied
