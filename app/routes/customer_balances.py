from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import (
    Account, Category, Payment, Product, ProductUnit, Sale, GeneralLedger,
    Customer, CustomerDebt, CustomerPayment
)
from app.utils.auth import token_required
from app.utils.gl_utils import post_to_ledger, generate_transaction_number
from sqlalchemy.orm import joinedload
from dateutil.relativedelta import relativedelta

customer_balances_bp = Blueprint('customer_balances', __name__, url_prefix='/customer_balances')

# -----------------------------------
# 1️⃣ GET all customer balances/debts
# # -----------------------------------
# @token_required
# @customer_balances_bp.route('/', methods=['GET'])
# def list_customer_balances():
#     debts = (
#         CustomerDebt.query
#         .options(joinedload(CustomerDebt.customer), joinedload(CustomerDebt.payments))
#         .filter(CustomerDebt.status != 9)
#         .all()
#     )

#     result = []
#     for d in debts:
#         db.session.query(Sale.)
#         # Calculate days overdue
#         days_overdue = (datetime.utcnow() - d.debt_date).days
#         payments_list = [
#             {
#                 "id": p.id,
#                 "amount": p.amount,
#                 "payment_date": p.payment_date,
#                 "payment_type": p.payment_type,
#                 "reference": p.reference,
#                 "status": p.status
#             }
#             for p in d.payments
#         ]
#         print(".customer_id  ",d.customer_id)
#         customer_names = db.session.query(Customer).filter(Customer.id==d.customer_id).first()
#         print("custiner details ",customer_names.to_dict())
#         result.append({
#             "id": d.id,
#             "customer_name": customer_names.name,
#             "customer_id":d.customer_id,
#             "debt_date": d.debt_date.strftime("%Y-%m-%d"),
#             "total_amount": d.total_amount,
#             "amount_paid": d.amount_paid,
#             # "customer":
#             "balance": d.debt_balance,
#             "payment_status": d.payment_status,
#             "days_overdue": days_overdue,
#             "payments": payments_list
#         })

#     return jsonify(result), 200



# # -----------------------------
# @token_required
# @customer_balances_bp.route('/', methods=['GET'])
# def list_customer_balances():
#     # ----------------- Get search query param -----------------
#     search = request.args.get('search', type=str)

#     # ----------------- Base query: all active debts -----------------
#     query = CustomerDebt.query.options(joinedload(CustomerDebt.customer)).filter(CustomerDebt.status != 9)

#     # ----------------- Apply search filter if provided -----------------
#     if search:
#         search_term = f"%{search}%"
#         query = query.join(Customer).filter(Customer.name.ilike(search_term))

#     debts = query.all()

#     result = []

#     for d in debts:
#         # ----------------- Calculate days overdue -----------------
#         days_overdue = (datetime.utcnow() - d.debt_date).days

#         # ----------------- Prepare payments list -----------------
#         payments_list = [
#             {
#                 "id": p.id,
#                 "amount": p.amount,
#                 "payment_date": p.payment_date.strftime("%Y-%m-%d") if p.payment_date else None,
#                 "payment_type": p.payment_type,
#                 "reference": p.reference,
#                 "status": p.status
#             }
#             for p in getattr(d, "payments", [])
#         ]

#         # ----------------- Get customer info -----------------
#         customer = d.customer
#         customer_name = customer.name if customer else "Walk-in"

#         # ----------------- Calculate new_balance from sales -----------------
#         pending_sales = (
#             Sale.query
#             .filter(
#                 Sale.customer_id == d.customer_id,
#                 Sale.payment_status.in_(["Pending", "Partial"]),
#                 Sale.status != 9
#             )
#             .all()
#         )
#         new_balance = sum(s.balance for s in pending_sales)

#         # ----------------- Append to result -----------------
#         result.append({
#             "id": d.id,
#             "customer_name": customer_name,
#             "customer_id": d.customer_id,
#             "debt_date": d.debt_date.strftime("%Y-%m-%d"),
#             "total_amount": d.total_amount,
#             "amount_paid": d.amount_paid,
#             "balance": d.debt_balance,
#             "new_balance": new_balance,
#             "payment_status": d.payment_status,
#             "days_overdue": days_overdue,
#             "payments": payments_list
#         })

#     return jsonify(result), 200



# -----------------------------
@token_required
@customer_balances_bp.route('/', methods=['GET'])
def list_customer_balances():
    """
    List all customer debts with optional search by customer name.
    Adds new_balance (sum of pending/partial sales balances).
    """
    try:
        search = request.args.get('search', type=str)

        # Base query: active debts only
        query = CustomerDebt.query.options(joinedload(CustomerDebt.customer)).filter(CustomerDebt.status != 9)

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.join(Customer).filter(Customer.name.ilike(search_term))

        debts = query.all()

        result = []

        for d in debts:
            # Days overdue
            days_overdue = (datetime.utcnow() - d.debt_date).days

            # Payments list
            payments_list = [
                {
                    "id": p.id,
                    "amount": p.amount,
                    "payment_date": p.payment_date.strftime("%Y-%m-%d") if p.payment_date else None,
                    "payment_type": p.payment_type,
                    "reference": p.reference,
                    "status": p.status
                }
                for p in getattr(d, "payments", [])
            ]

            # Customer info
            customer = d.customer
            customer_name = customer.name if customer else "Walk-in"

            # New balance: sum of all pending/partial sales for this customer
            pending_sales = (
                Sale.query
                .filter(
                    Sale.customer_id == d.customer_id,
                    Sale.payment_status.in_(["Pending", "Partial"]),
                    Sale.status != 9
                )
                .all()
            )
            new_balance = sum(s.balance for s in pending_sales)

            result.append({
                "id": d.id,
                "customer_name": customer_name,
                "customer_id": d.customer_id,
                "debt_date": d.debt_date.strftime("%Y-%m-%d"),
                "total_amount": d.total_amount,
                "amount_paid": d.amount_paid,
                "balance": d.debt_balance,
                "new_balance": new_balance if new_balance>=0 else 0,
                # "total "
                "payment_status": d.payment_status,
                "days_overdue": days_overdue,
                "payments": payments_list
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# -----------------------------------
# 2️⃣ POST - Create a new customer debt
# -----------------------------------
@token_required
@customer_balances_bp.route('/save', methods=['POST'])
def create_customer_debt():
    data = request.get_json()
    customer_id = data.get('customer_id')
    total_amount = float(data.get('total_amount', 0))
    balance = float(data.get('balance', 0))
    memo = data.get('memo', None)

    # Check customer or create one if not exists
    # customer = Customer.query.filter(Customer.id == ).first()
    # if not customer:
    #     customer = Customer(name=customer_name, status=1)
    #     db.session.add(customer)
    #     db.session.flush()

    # Generate transaction number
    txn_id, txn_str = generate_transaction_number('DEBT', transaction_date=datetime.utcnow())

    debt = CustomerDebt(
        customer_id=customer_id,
        total_amount=total_amount,
        debt_balance=balance,
        amount_paid=total_amount - balance,
        memo=memo or "Customer debt recorded",
        transaction_no=txn_id,
        payment_status="Pending" if balance > 0 else "Cleared",
        status=1
    )
    db.session.add(debt)

    entries = [
                {"account_id": 1100, "transaction_type": "Debit", "amount": total_amount},# receoavbale 
                {"account_id": 4010, "transaction_type": "Credit", "amount": total_amount},# sales revenue 
    ]
    gl_entries = post_to_ledger(entries, transaction_no_id=txn_id,
                                    description=f"customer Debt #{txn_id}", transaction_date=datetime.utcnow())
    db.session.commit()
    return jsonify({
        "message": "Customer debt recorded successfully",
        "transaction_no": txn_str,
        "customer_id": customer_id,
        "balance": balance
    }), 201


# -----------------------------------
# 3️⃣ POST - Record a customer payment
# -----------------------------------
# @token_required
# @customer_balances_bp.route('/payment', methods=['POST'])
# def record_customer_payment(current_user):
#     data = request.get_json()
#     debt_id = data.get('debt_id')
#     payment_account_id = data.get('payment_account_id')
#     amount_paid = float(data.get('amount_paid', 0))
#     payment_type = data.get('payment_type', 'Cash')
#     reference = data.get('reference', None)
#     payment_date_ui = data.get("paymemnt_date")  # note spelling matches frontend

#     # Fetch the debt (and related customer)
#     debt = CustomerDebt.query.get(debt_id)
#     if not debt:
#         return jsonify({"error": "Debt record not found"}), 404

#     customer = debt.customer  # get customer from debt
#     if not customer:
#         return jsonify({"error": "Associated customer not found"}), 404

#     if amount_paid < 0:
#         return jsonify({"error": "Amount must be greater than zero"}), 400

#     # Parse payment date
#     try:
#         payment_date = datetime.strptime(payment_date_ui, "%Y-%m-%d") if payment_date_ui else datetime.utcnow()
#     except ValueError:
#         return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

#     # Generate transaction number
#     txn_id, txn_str = generate_transaction_number('PAY', transaction_date=payment_date)

#     # --- Save Payment ---
#     payment = CustomerPayment(
#         customer_id=customer.id,
#         payment_date=payment_date,
#         debt_id=debt.id,
#         amount=amount_paid,
#         payment_account_id=payment_account_id,
#         payment_type=payment_type,
#         reference=reference,
#         transaction_no=txn_id,
#         status=1
#     )
#     db.session.add(payment)

#     # --- Update Debt ---
#     debt.amount_paid += amount_paid
#     debt.update_status()
#     db.session.add(debt)

#     # --- Double-entry posting ---
#     credit_account_code = int(payment_account_id)  # e.g., Cash/Bank
#     entries = [
#         {"account_id": credit_account_code, "transaction_type": "Debit", "amount": amount_paid},
#         {"account_id": 1100, "transaction_type": "Credit", "amount": amount_paid},  # Accounts Receivable
#     ]

#     gl_entries = post_to_ledger(entries, transaction_no_id=txn_id, transaction_date=payment_date, memo="Customer Payment")

#     db.session.commit()

#     return jsonify({
#         "message": "Customer payment recorded successfully",
#         "transaction_no": txn_str,
#         "debt_balance": debt.debt_balance,
#         "ledger_entries": gl_entries
#     }), 201
# @token_required
# @customer_balances_bp.route('/payment', methods=['POST'])
# def record_customer_payment(current_user):
#     data = request.get_json()
#     debt_id = data.get('debt_id')
#     payment_account_id = data.get('payment_account_id')
#     amount_paid = float(data.get('amount_paid', 0))
#     payment_type = data.get('payment_type', 'Cash')
#     reference = data.get('reference', None)
#     payment_date_ui = data.get("paymemnt_date")  # note spelling matches frontend

#     # Fetch the debt (and related customer)
#     debt = CustomerDebt.query.get(debt_id)
#     if not debt:
#         return jsonify({"error": "Debt record not found"}), 404

#     customer = debt.customer  # get customer from debt
#     if not customer:
#         return jsonify({"error": "Associated customer not found"}), 404

#     if amount_paid < 0:
#         return jsonify({"error": "Amount must be greater than zero"}), 400

#     # Parse payment date
#     try:
#         payment_date = datetime.strptime(payment_date_ui, "%Y-%m-%d") if payment_date_ui else datetime.utcnow()
#     except ValueError:
#         return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

#     # Generate transaction number
#     txn_id, txn_str = generate_transaction_number('PAY', transaction_date=payment_date)

#     # --- Save Payment ---
#     payment = CustomerPayment(
#         customer_id=customer.id,
#         payment_date=payment_date,
#         debt_id=debt.id,
#         amount=amount_paid,
#         payment_account_id=payment_account_id,
#         payment_type=payment_type,
#         reference=reference,
#         transaction_no=txn_id,
#         status=1
#     )
#     db.session.add(payment)

#     # --- Update Debt ---
#     debt.amount_paid += amount_paid
#     debt.update_status()
#     db.session.add(debt)

#     # --- Double-entry posting ---
#     credit_account_code = int(payment_account_id)  # e.g., Cash/Bank
#     entries = [
#         {"account_id": credit_account_code, "transaction_type": "Debit", "amount": amount_paid},
#         {"account_id": 1100, "transaction_type": "Credit", "amount": amount_paid},  # Accounts Receivable
#     ]

#     gl_entries = post_to_ledger(entries, transaction_no_id=txn_id, transaction_date=payment_date, memo="Customer Payment")

#     db.session.commit()

#     return jsonify({
#         "message": "Customer payment recorded successfully",
#         "transaction_no": txn_str,
#         "debt_balance": debt.debt_balance,
#         "ledger_entries": gl_entries
#     }), 201



@token_required
@customer_balances_bp.route('/payment', methods=['POST'])
def record_customer_payment():
    data = request.get_json()
    debt_id = data.get('debt_id')
    payment_account_id = data.get('payment_account_id')
    amount_paid = float(data.get('amount_paid', 0))
    payment_type = data.get('payment_type', 'Cash')
    reference = data.get('reference', 'paid')
    payment_date_ui = data.get("paymemnt_date")  # note spelling matches frontend

    # Fetch the debt (and related customer)
    debt = CustomerDebt.query.get(debt_id)
    if not debt:
        return jsonify({"error": "Debt record not found"}), 404

    customer = debt.customer  # get customer from debt
    if not customer:
        return jsonify({"error": "Associated customer not found"}), 404

    if amount_paid < 0:
        return jsonify({"error": "Amount must be greater than zero"}), 400

    # Parse payment date
    try:
        payment_date = datetime.strptime(payment_date_ui, "%Y-%m-%d") if payment_date_ui else datetime.utcnow()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Generate transaction number
    txn_id, txn_str = generate_transaction_number('PAY', transaction_date=payment_date)

    # --- Save Payment ---
    payment = CustomerPayment(
        customer_id=customer.id,
        payment_date=payment_date,
        debt_id=debt.id,
        amount=amount_paid,
        payment_account_id=payment_account_id,
        payment_type=payment_type,
        reference=reference,
        transaction_no=txn_id,
        status=1
    )
    db.session.add(payment)

    # --- Update Debt ---
    debt.amount_paid += amount_paid
    debt.update_status()
    db.session.add(debt)

    # --- Double-entry posting ---
    credit_account_code = int(payment_account_id)  # e.g., Cash/Bank
    payment_account_code = Account.query.filter(Account.id==credit_account_code).first().code
    entries = [
        {"account_id": payment_account_code, "transaction_type": "Debit", "amount": amount_paid},
        {"account_id": 1100, "transaction_type": "Credit", "amount": amount_paid},  # Accounts Receivable
    ]

    gl_entries = post_to_ledger(entries, transaction_no_id=txn_id, transaction_date=payment_date, description="Customer Payment")

    db.session.commit()

    return jsonify({
        "message": "Customer payment recorded successfully",
        "transaction_no": txn_str,
        "debt_balance": debt.debt_balance,
        "amount_paid":amount_paid,
        "payment_id":payment.id,
        # "ledger_entries": gl_entries
    }), 201



@token_required
@customer_balances_bp.route('/delete/<int:debt_id>', methods=['DELETE'])
def delete_customer_debt(debt_id):
    """
    Soft delete a customer debt and post reversal entries
    """
    data = request.get_json()
    # debt_id = data.get('debt_id')
    reason = data.get('reason', 'Debt deleted')

    # --- Validate debt record ---
    debt = CustomerDebt.query.get(debt_id)
    if not debt:
        return jsonify({"error": "Debt record not found"}), 404
    if debt.status == 9:
        return jsonify({"error": "Debt already deleted"}), 400

    # --- Soft delete ---
    debt.status = 9
    debt.memo = f"{reason} (Soft deleted)"
    db.session.add(debt)

    # --- Generate reversal transaction number ---
    txn_id, txn_str = generate_transaction_number('REV', transaction_date=datetime.utcnow())

    # --- Reverse double-entry ---
    # Original when creating debt was:
    #   Debit 1100 (Accounts Receivable)
    #   Credit 4010 (Sales Revenue)
    # To reverse → swap them.
    entries = [
        {"account_id": 4010, "transaction_type": "Debit", "amount": float(debt.total_amount)},
        {"account_id": 1100, "transaction_type": "Credit", "amount": float(debt.total_amount)},
    ]

    gl_entries = post_to_ledger(
        entries,
        transaction_no_id=txn_id,
        description=f"Reversal of deleted customer debt #{debt.id}",
        transaction_date=datetime.utcnow()
    )

    db.session.commit()

    return jsonify({
        "message": "Customer debt deleted (soft delete) and reversal entries posted",
        "debt_id": debt.id,
        "transaction_no": txn_str,
        # "reversal_entries": gl_entries
    }), 200
