from flask import Blueprint, jsonify
from app.models import AccountTypeEnum, Category, GeneralLedger, ProductUnit, PurchaseOrderItem, SaleItem, PurchaseOrder, Expense,Customer, Supplier, Sale, PurchaseOrder, Product, Account
from app import db
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

from sqlalchemy.orm import joinedload

from app.utils.auth import token_required
from flask import request, jsonify
from sqlalchemy import func, and_, cast, String,or_,case

from app.utils.gl_utils import get_latest_purchase_price, get_latest_purchase_price_no_rounds



reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

# ------------------ General Ledger ------------------
@token_required
@reports_bp.route('/general-ledger', methods=['GET'])
def general_ledger():
    # ---------- Query params ----------
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
    except ValueError:
        return jsonify({"error": "page and page_size must be integers"}), 400

    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    search = request.args.get('search', '').strip()

    filters = [GeneralLedger.status != 9]

    # ---------- Date filters ----------
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            filters.append(GeneralLedger.transaction_date >= start_date)
        except ValueError:
            return jsonify({"error": "start_date must be YYYY-MM-DD"}), 400

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            filters.append(GeneralLedger.transaction_date <= end_date)
        except ValueError:
            return jsonify({"error": "end_date must be YYYY-MM-DD"}), 400

    # ---------- Base query ----------
    query = db.session.query(
        GeneralLedger.id,
        GeneralLedger.transaction_date,
        GeneralLedger.transaction_type,
        GeneralLedger.amount,
        GeneralLedger.description,
        Account.name.label('account_name'),
        Account.account_type,
        Account.account_subtype
    ).join(Account, GeneralLedger.account_id == Account.id).filter(*filters)

    # ---------- Search ----------
    if search:
        # Convert search to lowercase for case-insensitive search
        search_str = f"%{search.lower()}%"
        query = query.filter(
            or_(
                db.func.lower(Account.name).ilike(search_str),
                db.func.lower(GeneralLedger.description).ilike(search_str),
                db.func.lower(Account.account_subtype).ilike(search_str),
                db.func.lower(Account.account_type.cast(db.String)).ilike(search_str)
            )
        )

    # ---------- Count for pagination ----------
    total_records = query.count()

    # ---------- Apply ordering and pagination ----------
    ledgers = query.order_by(GeneralLedger.id.desc()) \
                   .offset((page - 1) * page_size) \
                   .limit(page_size) \
                   .all()

    # ---------- Format response ----------
    result = [{
        "id": g.id,
        "transaction_date": g.transaction_date.strftime('%Y-%m-%d'),
        "transaction_type": g.transaction_type,
        "amount": float(g.amount),
        "description": g.description,
        "account_name": g.account_name,
        "account_type": g.account_type.name if hasattr(g.account_type, 'name') else str(g.account_type),
        "account_subtype": g.account_subtype
    } for g in ledgers]

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total_records": total_records,
        "total_pages": (total_records + page_size - 1) // page_size,
        "data": result
    })

#
# ------------------ Trial Balance (Professional) ------------------
# from flask import Blueprint, jsonify, request
# from sqlalchemy import func, case
# from app import db
# from app.models import Account, GeneralLedger
# from app.utils.auth import token_required

# reports_bp = Blueprint('reports_bp', __name__)
# ------------------ Trial Balance Professional ------------------


# ------------------ Hierarchical Trial Balance (with Debit/Credit Columns) ------------------
@token_required
@reports_bp.route("/trial-balance", methods=["GET"])
def trial_balance():
    """
    Returns a hierarchical Trial Balance with Opening, Movement, and Closing balances.
    Includes separate Debit and Credit columns and parent roll-ups.
    """

    from sqlalchemy import and_, case

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
    except ValueError:
        return jsonify({"error": "Dates must be in YYYY-MM-DD format"}), 400

    filters = [Account.status != 9]
    gl_filters = [GeneralLedger.status != 9]

    # --- Subqueries ---
    # Opening balances (split debit/credit)
    opening_query = (
        db.session.query(
            GeneralLedger.account_id,
            func.sum(case((GeneralLedger.amount > 0, GeneralLedger.amount), else_=0)).label("opening_debit"),
            func.sum(case((GeneralLedger.amount < 0, -GeneralLedger.amount), else_=0)).label("opening_credit"),
        )
        .filter(*gl_filters)
        .filter(GeneralLedger.transaction_date < start_date if start_date else True)
        .group_by(GeneralLedger.account_id)
        .subquery()
    )

    # Movement within the period
    movement_query = (
        db.session.query(
            GeneralLedger.account_id,
            func.sum(case((GeneralLedger.amount > 0, GeneralLedger.amount), else_=0)).label("movement_debit"),
            func.sum(case((GeneralLedger.amount < 0, -GeneralLedger.amount), else_=0)).label("movement_credit"),
        )
        .filter(*gl_filters)
        .filter(
            and_(
                GeneralLedger.transaction_date >= start_date if start_date else True,
                GeneralLedger.transaction_date <= end_date if end_date else True,
            )
        )
        .group_by(GeneralLedger.account_id)
        .subquery()
    )

    # --- Fetch accounts ---
    raw_accounts = (
        db.session.query(
            Account.id,
            Account.name,
            Account.account_type,
            Account.parent_id,
            func.coalesce(opening_query.c.opening_debit, 0).label("opening_debit"),
            func.coalesce(opening_query.c.opening_credit, 0).label("opening_credit"),
            func.coalesce(movement_query.c.movement_debit, 0).label("movement_debit"),
            func.coalesce(movement_query.c.movement_credit, 0).label("movement_credit"),
        )
        .outerjoin(opening_query, opening_query.c.account_id == Account.id)
        .outerjoin(movement_query, movement_query.c.account_id == Account.id)
        .filter(*filters)
        .all()
    )

    # --- Build dict ---
    accounts_dict = {}
    for a in raw_accounts:
        opening_balance = a.opening_debit - a.opening_credit
        movement_balance = a.movement_debit - a.movement_credit
        closing_balance = opening_balance + movement_balance

        accounts_dict[a.id] = {
            "account_id": a.id,
            "account_name": a.name,
            "account_type": a.account_type.value if hasattr(a.account_type, "value") else str(a.account_type),
            "parent_id": a.parent_id,
            "opening_debit": float(a.opening_debit or 0),
            "opening_credit": float(a.opening_credit or 0),
            "movement_debit": float(a.movement_debit or 0),
            "movement_credit": float(a.movement_credit or 0),
            "closing_balance": closing_balance,
            "children": []
        }

    # --- Build hierarchy ---
    root_accounts = []
    for acc in accounts_dict.values():
        if acc["parent_id"] and acc["parent_id"] in accounts_dict:
            accounts_dict[acc["parent_id"]]["children"].append(acc)
        else:
            root_accounts.append(acc)

    # --- Recursive roll-up ---
    def roll_up(acc):
        for child in acc["children"]:
            roll_up(child)
            acc["opening_debit"] += child["opening_debit"]
            acc["opening_credit"] += child["opening_credit"]
            acc["movement_debit"] += child["movement_debit"]
            acc["movement_credit"] += child["movement_credit"]
            acc["closing_balance"] += child["closing_balance"]

    for r in root_accounts:
        roll_up(r)

    # --- Group and subtotal ---
    grouped = {}
    for acc in root_accounts:
        atype = acc["account_type"]
        grouped.setdefault(atype, {
            "account_type": atype,
            "accounts": [],
            "subtotal_opening_debit": 0,
            "subtotal_opening_credit": 0,
            "subtotal_movement_debit": 0,
            "subtotal_movement_credit": 0,
            "subtotal_closing": 0
        })
        g = grouped[atype]
        g["accounts"].append(acc)
        g["subtotal_opening_debit"] += acc["opening_debit"]
        g["subtotal_opening_credit"] += acc["opening_credit"]
        g["subtotal_movement_debit"] += acc["movement_debit"]
        g["subtotal_movement_credit"] += acc["movement_credit"]
        g["subtotal_closing"] += acc["closing_balance"]

    totals = {
        "total_opening_debit": sum(g["subtotal_opening_debit"] for g in grouped.values()),
        "total_opening_credit": sum(g["subtotal_opening_credit"] for g in grouped.values()),
        "total_movement_debit": sum(g["subtotal_movement_debit"] for g in grouped.values()),
        "total_movement_credit": sum(g["subtotal_movement_credit"] for g in grouped.values()),
    }

    return jsonify({
        "period": {"start_date": start_date_str, "end_date": end_date_str},
        "groups": grouped,
        "totals": totals,
    })




# ---------
@token_required
@reports_bp.route("/trial-balance-old ", methods=["GET"])
def trial_balance_old():
    """
    Returns a professional Trial Balance report.
    Includes Opening, Movement, and Closing balances for each account.
    Grouped by account type, with subtotals and grand totals.
    Supports ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """

    from sqlalchemy import case, and_

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
    except ValueError:
        return jsonify({"error": "Dates must be in YYYY-MM-DD format"}), 400

    # Base filters
    filters = [Account.status != 9]
    gl_filters = [GeneralLedger.status != 9]

    # --- Subqueries ---
    # Opening balance: all transactions before the start date
    opening_query = (
        db.session.query(
            GeneralLedger.account_id,
            func.coalesce(func.sum(GeneralLedger.amount), 0).label("opening_balance")
        )
        .filter(*gl_filters)
        .filter(GeneralLedger.transaction_date < start_date if start_date else True)
        .group_by(GeneralLedger.account_id)
        .subquery()
    )

    # Period movement: transactions within the date range
    movement_query = (
        db.session.query(
            GeneralLedger.account_id,
            func.coalesce(func.sum(GeneralLedger.amount), 0).label("movement")
        )
        .filter(*gl_filters)
        .filter(
            and_(
                GeneralLedger.transaction_date >= start_date if start_date else True,
                GeneralLedger.transaction_date <= end_date if end_date else True,
            )
        )
        .group_by(GeneralLedger.account_id)
        .subquery()
    )

    # --- Main Query ---
    accounts = (
        db.session.query(
            Account.id.label("account_id"),
            Account.name.label("account_name"),
            Account.account_type.label("account_type"),
            func.coalesce(opening_query.c.opening_balance, 0).label("opening_balance"),
            func.coalesce(movement_query.c.movement, 0).label("movement"),
        )
        .outerjoin(opening_query, opening_query.c.account_id == Account.id)
        .outerjoin(movement_query, movement_query.c.account_id == Account.id)
        .filter(*filters)
        .all()
    )

    # --- Process Results ---
    report_data = []
    for acc in accounts:
        opening = float(acc.opening_balance or 0)
        movement = float(acc.movement or 0)
        closing = opening + movement

        # Determine debit/credit split
        debit = movement if movement > 0 else 0
        credit = abs(movement) if movement < 0 else 0

        report_data.append({
            "account_id": acc.account_id,
            "account_name": acc.account_name,
            "account_type": acc.account_type.value if hasattr(acc.account_type, "value") else str(acc.account_type),
            "opening_balance": opening,
            "movement": movement,
            "closing_balance": closing,
            "debit": debit,
            "credit": credit,
        })

    # --- Grouping & Subtotals ---
    grouped = {}
    for row in report_data:
        atype = row["account_type"]
        if atype not in grouped:
            grouped[atype] = {
                "account_type": atype,
                "accounts": [],
                "subtotal_opening": 0,
                "subtotal_debit": 0,
                "subtotal_credit": 0,
                "subtotal_movement": 0,
                "subtotal_closing": 0,
            }

        g = grouped[atype]
        g["accounts"].append(row)
        g["subtotal_opening"] += row["opening_balance"]
        g["subtotal_debit"] += row["debit"]
        g["subtotal_credit"] += row["credit"]
        g["subtotal_movement"] += row["movement"]
        g["subtotal_closing"] += row["closing_balance"]

    # --- Grand Totals ---
    totals = {
        "grand_opening": sum(g["subtotal_opening"] for g in grouped.values()),
        "grand_debit": sum(g["subtotal_debit"] for g in grouped.values()),
        "grand_credit": sum(g["subtotal_credit"] for g in grouped.values()),
        "grand_movement": sum(g["subtotal_movement"] for g in grouped.values()),
        "grand_closing": sum(g["subtotal_closing"] for g in grouped.values()),
    }

    # --- Sort groups for consistent display ---
    group_order = ["ASSET", "LIABILITY", "EQUITY", "REVENUE", "EXPENSE"]
    ordered_groups = [grouped[k] for k in group_order if k in grouped] + [
        v for k, v in grouped.items() if k not in group_order
    ]

    return jsonify({
        "period": {"start_date": start_date_str, "end_date": end_date_str},
        "groups": ordered_groups,
        "totals": totals,
    })


# ------------------ Profit & Loss ------------------
@token_required
@reports_bp.route('/profit-loss', methods=['GET'])
def profit_loss():
    # Total sales
    total_sales = db.session.query(func.coalesce(func.sum(GeneralLedger.amount), 0)).join(Account).filter(
        GeneralLedger.status != 9,
        Account.account_type.ilike('%Revenue%')
    ).scalar()

    # Total expenses
    total_expenses = db.session.query(func.coalesce(func.sum(GeneralLedger.amount), 0)).join(Account).filter(
        GeneralLedger.status != 9,
        Account.account_type.ilike('%Expense%')
    ).scalar()

    result = {
        "total_sales": float(total_sales),
        "total_expenses": float(total_expenses),
        "net_profit": float(total_sales - total_expenses)
    }

    return jsonify(result)

# ------------------ Cash Flow ------------------
# @token_required
# @reports_bp.route('/cash-flow', methods=['GET'])
# def cash_flow():
#     # Cash inflows: Sales
#     cash_inflow = db.session.query(func.coalesce(func.sum(GeneralLedger.amount), 0)).join(Account).filter(
#         GeneralLedger.status != 9,
#         Account.account_type.ilike('%Cash%')
#     ).scalar()

#     # Cash outflows: Purchases + Expenses
#     cash_outflow = db.session.query(func.coalesce(func.sum(GeneralLedger.amount), 0)).join(Account).filter(
#         GeneralLedger.status != 9,
#         Account.account_type.ilike('%Payable%') | Account.account_type.ilike('%Expense%')
#     ).scalar()

#     result = {
#         "cash_inflow": float(cash_inflow),
#         "cash_outflow": float(cash_outflow),
#         "net_cash_flow": float(cash_inflow - cash_outflow)
#     }

#     return jsonify(result)

# from flask import Blueprint, request, jsonify
# from flask_jwt_extended import jwt_required as token_required
# from sqlalchemy import func, and_, cast, String
# from datetime import datetime
# from app import db
# from app.models import GeneralLedger, Account

# reports_bp = Blueprint("reports_bp", __name__)

@token_required
@reports_bp.route("/cash-flow", methods=["GET"])
def cash_flow():
    """
    Returns a hierarchical cash flow statement with Opening, Movement, and Closing balances.
    Child accounts are rolled up into their parent accounts.
    Groups by Cash Inflows and Cash Outflows.
    """

    # --- Parse optional date filters ---
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
    except ValueError:
        return jsonify({"error": "Dates must be in YYYY-MM-DD format"}), 400

    gl_filters = [GeneralLedger.status != 9]
    acc_filters = [Account.status != 9]

    # --- Opening balances (before period) ---
    opening_query = (
        db.session.query(
            GeneralLedger.account_id,
            func.coalesce(func.sum(GeneralLedger.amount), 0).label("opening_balance")
        )
        .filter(*gl_filters)
        .filter(GeneralLedger.transaction_date < start_date if start_date else True)
        .group_by(GeneralLedger.account_id)
        .subquery()
    )

    # --- Movement during period ---
    movement_query = (
        db.session.query(
            GeneralLedger.account_id,
            func.coalesce(func.sum(GeneralLedger.amount), 0).label("movement")
        )
        .filter(*gl_filters)
        .filter(
            and_(
                GeneralLedger.transaction_date >= start_date if start_date else True,
                GeneralLedger.transaction_date <= end_date if end_date else True
            )
        )
        .group_by(GeneralLedger.account_id)
        .subquery()
    )

    # --- Fetch all accounts with balances ---
    raw_accounts = (
        db.session.query(
            Account.id,
            Account.name,
            Account.account_type,
            Account.parent_id,
            cast(Account.account_type, String).label("account_type_str"),
            func.coalesce(opening_query.c.opening_balance, 0).label("opening_balance"),
            func.coalesce(movement_query.c.movement, 0).label("movement")
        )
        .outerjoin(opening_query, opening_query.c.account_id == Account.id)
        .outerjoin(movement_query, movement_query.c.account_id == Account.id)
        .filter(*acc_filters)
        .all()
    )

    # --- Build accounts dict ---
    accounts_dict = {}
    for a in raw_accounts:
        opening = float(a.opening_balance or 0)
        movement = float(a.movement or 0)
        closing = opening + movement
        accounts_dict[a.id] = {
            "account_id": a.id,
            "account_name": a.name,
            "account_type": a.account_type_str.upper(),
            "parent_id": a.parent_id,
            "opening_balance": opening,
            "movement": movement,
            "closing_balance": closing,
            "children": []
        }

    # --- Build hierarchy ---
    root_accounts = []
    for acc in accounts_dict.values():
        if acc["parent_id"] and acc["parent_id"] in accounts_dict:
            accounts_dict[acc["parent_id"]]["children"].append(acc)
        else:
            root_accounts.append(acc)

    # --- Recursive roll-up ---
    def roll_up(account):
        for child in account["children"]:
            roll_up(child)
            account["opening_balance"] += child["opening_balance"]
            account["movement"] += child["movement"]
            account["closing_balance"] += child["closing_balance"]

    for root in root_accounts:
        roll_up(root)

    # --- Classify inflows/outflows ---
    INFLOW_TYPES = ["ASSET", "REVENUE"]       # green
    OUTFLOW_TYPES = ["LIABILITY", "EXPENSE"] # red

    inflows = []
    outflows = []

    for acc in root_accounts:
        if acc["account_type"] in INFLOW_TYPES:
            inflows.append(acc)
        elif acc["account_type"] in OUTFLOW_TYPES:
            # Optionally invert outflows for visual consistency
            acc["opening_balance"] *= -1
            acc["movement"] *= -1
            acc["closing_balance"] *= -1
            outflows.append(acc)
        else:
            # If unknown type, treat as outflow
            acc["opening_balance"] *= -1
            acc["movement"] *= -1
            acc["closing_balance"] *= -1
            outflows.append(acc)

    # --- Totals ---
    def sum_group(accounts):
        total_opening = sum(a["opening_balance"] for a in accounts)
        total_movement = sum(a["movement"] for a in accounts)
        total_closing = sum(a["closing_balance"] for a in accounts)
        return {"total_opening": total_opening, "total_movement": total_movement, "total_closing": total_closing}

    totals = {
        "inflows": sum_group(inflows),
        "outflows": sum_group(outflows),
        "net": {
            "opening_balance": sum_group(inflows)["total_opening"] - sum_group(outflows)["total_opening"],
            "movement": sum_group(inflows)["total_movement"] - sum_group(outflows)["total_movement"],
            "closing_balance": sum_group(inflows)["total_closing"] - sum_group(outflows)["total_closing"]
        }
    }

    return jsonify({
        "period": {"start_date": start_date_str, "end_date": end_date_str},
        "inflows": inflows,
        "outflows": outflows,
        "totals": totals
    })

# _------------------------------------------

# from flask import Blueprint, jsonify
# from app.models import Customer, Supplier, Sale, PurchaseOrder, Product, Expense, db
# from sqlalchemy import func
# from datetime import datetime, timedelta

# reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

# ------------------ Debtors Report ------------------
@token_required
@reports_bp.route('/debtors-report-old', methods=['GET'])
def debtors_report_old():
    # Only include customers with outstanding balance > 0
    debtors = db.session.query(
        Customer.id,
        Customer.name,
        Customer.phone,
        func.coalesce(func.sum(Sale.balance), 0).label('balance')
    ).join(Sale, Sale.customer_id == Customer.id).filter(
        Customer.status != 9,
        Sale.status != 9
    ).group_by(Customer.id).having(func.sum(Sale.balance) > 0).all()

    result = [{
        "id": d.id,
        "name": d.name,
        "phone": d.phone,
        "balance": float(d.balance)
    } for d in debtors]

    return jsonify(result)

@token_required
@reports_bp.route('/debtors-aging', methods=['GET'])
def debtors_aging_report():
    """
    Returns a professional Debtors Aging Report:
    - Buckets: 0-30, 31-60, 61-90, >90 days
    - Includes per-customer invoice list with days outstanding
    - Only customers with outstanding balances > 0
    - Supports pagination: ?page=1&page_size=10
    """
    # --- Optional "as of" date ---
    as_of_str = request.args.get("as_of")
    as_of = datetime.strptime(as_of_str, "%Y-%m-%d") if as_of_str else datetime.utcnow()

    # --- Pagination parameters ---
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    offset = (page - 1) * page_size

    # --- Subquery: customers with outstanding balances ---
    subq = (
        db.session.query(
            Sale.customer_id,
            func.coalesce(func.sum(Sale.balance), 0).label('total_balance')
        )
        .filter(Sale.status != 9, Sale.balance > 0)
        .group_by(Sale.customer_id)
        .subquery()
    )

    # --- Total count for pagination metadata ---
    total_customers = db.session.query(func.count(subq.c.customer_id)).scalar()

    # --- Fetch paginated customers ---
    customers = (
        db.session.query(
            Customer.id.label('customer_id'),
            Customer.name,
            Customer.phone,
            Customer.email,
            Customer.address,
            func.coalesce(subq.c.total_balance, 0).label('balance')
        )
        .outerjoin(subq, subq.c.customer_id == Customer.id)
        .filter(Customer.status != 9, subq.c.total_balance > 0)
        .order_by(Customer.name)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # --- Prepare aging buckets ---
    bucket_case = case(
        (func.date_part('day', func.age(as_of, Sale.sale_date)) <= 30, '0-30'),
        (func.date_part('day', func.age(as_of, Sale.sale_date)) <= 60, '31-60'),
        (func.date_part('day', func.age(as_of, Sale.sale_date)) <= 90, '61-90'),
        else_='>90'
    )

    report = []
    for c in customers:
        # Fetch invoices per customer
        invoices = db.session.query(
            Sale.id.label('invoice_id'),
            Sale.sale_number,
            Sale.sale_date,
            Sale.total_amount,
            Sale.total_paid,
            Sale.balance,
            func.date_part('day', func.age(as_of, Sale.sale_date)).label('days_outstanding'),
            bucket_case.label('aging_bucket')
        ).filter(
            Sale.customer_id == c.customer_id,
            Sale.status != 9,
            Sale.balance > 0
        ).order_by(Sale.sale_date).all()

        invoice_list = [{
            "invoice_id": inv.invoice_id,
            "sale_number": inv.sale_number,
            "sale_date": inv.sale_date.strftime("%Y-%m-%d"),
            "total_amount": float(inv.total_amount),
            "total_paid": float(inv.total_paid),
            "balance": float(inv.balance),
            "days_outstanding": int(inv.days_outstanding),
            "aging_bucket": inv.aging_bucket
        } for inv in invoices]

        # Compute total balance per customer
        total_balance = sum(inv["balance"] for inv in invoice_list)

        report.append({
            "customer_id": c.customer_id,
            "name": c.name,
            "phone": c.phone,
            "email": c.email,
            "address": c.address,
            "total_balance": total_balance,
            "invoices": invoice_list
        })

    return jsonify({
        "as_of": as_of.strftime("%Y-%m-%d"),
        "page": page,
        "page_size": page_size,
        "total_customers": total_customers,
        "total_pages": (total_customers + page_size - 1) // page_size,
        "report": report
    })

# ------------------ Creditors Report ------------------
# @token_required
# @reports_bp.route('/creditors-report', methods=['GET'])
# def creditors_report():
#     # Only include suppliers with unpaid purchase orders
#     creditors = db.session.query(
#         Supplier.id,
#         Supplier.name,
#         Supplier.contact,
#         func.coalesce(func.sum(PurchaseOrder.total_balance), 0).label('balance')
#     ).join(PurchaseOrder, PurchaseOrder.supplier_id == Supplier.id).filter(
#         Supplier.status != 9,
#         PurchaseOrder.status != 9
#     ).group_by(Supplier.id).having(func.sum(PurchaseOrder.total_balance) > 0).all()

#     result = [{
#         "id": c.id,
#         "name": c.name,
#         "phone": c.contact,
#         "balance": float(c.balance)
#     } for c in creditors]

#     return jsonify(result)
# -------------------------------
@token_required
@reports_bp.route('/creditors-aging', methods=['GET'])
def creditors_aging_report():
    """
    Professional Creditor Aging Report:
    - Buckets: 0-30, 31-60, 61-90, >90 days
    - Includes per-supplier purchase order list
    - Only suppliers with outstanding balances > 0
    - Supports pagination: ?page=1&page_size=10
    """
    # --- "As of" date ---
    as_of_str = request.args.get("as_of")
    as_of = datetime.strptime(as_of_str, "%Y-%m-%d") if as_of_str else datetime.utcnow()

    # --- Pagination ---
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    offset = (page - 1) * page_size

    # --- Subquery: suppliers with outstanding balances ---
    subq = (
        db.session.query(
            PurchaseOrder.supplier_id,
            func.coalesce(func.sum(PurchaseOrder.total_balance), 0).label("total_balance")
        )
        .filter(PurchaseOrder.status != 9, PurchaseOrder.total_balance > 0)
        .group_by(PurchaseOrder.supplier_id)
        .subquery()
    )

    # --- Total supplier count ---
    total_suppliers = db.session.query(func.count(subq.c.supplier_id)).scalar()

    # --- Fetch paginated suppliers ---
    suppliers = (
        db.session.query(
            Supplier.id.label("supplier_id"),
            Supplier.name,
            Supplier.contact,
            Supplier.email,
            # Supplier.,
            func.coalesce(subq.c.total_balance, 0).label("balance")
        )
        .outerjoin(subq, subq.c.supplier_id == Supplier.id)
        .filter(Supplier.status != 9, subq.c.total_balance > 0)
        .order_by(Supplier.name)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # --- Aging buckets ---
    aging_case = case(
        (func.date_part("day", func.age(as_of, PurchaseOrder.purchase_date)) <= 30, "0-30"),
        (func.date_part("day", func.age(as_of, PurchaseOrder.purchase_date)) <= 60, "31-60"),
        (func.date_part("day", func.age(as_of, PurchaseOrder.purchase_date)) <= 90, "61-90"),
        else_=">90"
    )

    report = []
    for s in suppliers:
        # Fetch purchase orders per supplier
        pos = db.session.query(
            PurchaseOrder.id.label("po_id"),
            PurchaseOrder.invoice_number,
            PurchaseOrder.purchase_date,
            PurchaseOrder.total_amount,
            PurchaseOrder.total_paid,
            PurchaseOrder.total_balance,
            func.date_part("day", func.age(as_of, PurchaseOrder.purchase_date)).label("days_outstanding"),
            aging_case.label("aging_bucket")
        ).filter(
            PurchaseOrder.supplier_id == s.supplier_id,
            PurchaseOrder.status != 9,
            PurchaseOrder.total_balance > 0
        ).order_by(PurchaseOrder.purchase_date).all()

        po_list = [{
            "po_id": po.po_id,
            "invoice_number": po.invoice_number,
            "purchase_date": po.purchase_date.strftime("%Y-%m-%d"),
            "total_amount": float(po.total_amount),
            "total_paid": float(po.total_paid),
            "balance": float(po.total_balance),
            "days_outstanding": int(po.days_outstanding),
            "aging_bucket": po.aging_bucket
        } for po in pos]

        total_balance = sum(po["balance"] for po in po_list)

        report.append({
            "supplier_id": s.supplier_id,
            "name": s.name,
            "contact": s.contact,
            "email": s.email,
            # "address": s.address,
            "total_balance": total_balance,
            "purchase_orders": po_list
        })

    return jsonify({
        "as_of": as_of.strftime("%Y-%m-%d"),
        "page": page,
        "page_size": page_size,
        "total_suppliers": total_suppliers,
        "total_pages": (total_suppliers + page_size - 1) // page_size,
        "report": report
    })



# ------------------ Out of Stock ------------------
@token_required
@reports_bp.route('/out-of-stock', methods=['GET'])
def out_of_stock():
    products = db.session.query(Product,Category).join(Category,Product.category_id==Category.id).filter(Product.status != 9, Product.quantity <= 0).all()
    result = [{
        "id": p.id,
        "name": p.name,
        "sku": p.sku,
        "category_name": cat.name if cat.id else "N/A",
        "quantity": p.quantity
    } for p,cat in products]
    return jsonify(result)

# ------------------ Stock List ------------------
@token_required

@reports_bp.route('/stock-list', methods=['GET'])
def stock_list():
    # Use joinedload to avoid N+1 queries
    products = db.session.query(Product,Category).join(Category,Product.category_id==Category.id).filter(Product.status != 9).all()

    result = []
    for p, cat in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "category_name": cat.name if cat.id else "N/A",
            "quantity": p.quantity
        })

    return jsonify(result)

# ------------------ Consumption List ------------------
@token_required
@reports_bp.route('/consumption-list', methods=['GET'])
def consumption_list():
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Get sales in the last 7 days that are active
    sales = db.session.query(Sale).filter(Sale.status != 9, Sale.sale_date >= seven_days_ago).all()
    
    result = []

    for sale in sales:
        for item in sale.items:  # Loop through SaleItems
            result.append({
                "id": item.id,
                "product_name": item.product_name or (item.product.name if item.product else "N/A"),
                "quantity_sold": item.quantity,
                "total_amount": float(item.total_price),
                "sale_date": sale.sale_date.strftime('%Y-%m-%d')
            })
    
    return jsonify(result)

# ------------------ Performance List ------------------
@token_required
@reports_bp.route('/performance-list', methods=['GET'])
def performance_list():
    # Best performing products by revenue
    performance = (
        db.session.query(
            Product.id,
            Product.name,
            func.coalesce(func.sum(SaleItem.total_price), 0).label('total_revenue')
        )
        .join(SaleItem, SaleItem.product_id == Product.id)
        .filter(Product.status != 9, SaleItem.status != 9)
        .group_by(Product.id)
        .order_by(func.sum(SaleItem.total_price).desc())
        .all()
    )

    result = [{
        "product_id": p.id,
        "product_name": p.name,
        "total_revenue": float(p.total_revenue)
    } for p in performance]

    return jsonify(result)

# ------------------ Sales List ------------------
@token_required
@reports_bp.route('/sales-list', methods=['GET'])
def sales_list():
    sales = db.session.query(Sale).filter(Sale.status != 9).all()
    result = [{
        "id": s.id,
        "product_name": s.product.name if s.product else "N/A",
        "quantity": s.quantity,
        "total_amount": float(s.total_amount),
        "sale_date": s.sale_date.strftime('%Y-%m-%d')
    } for s in sales]
    return jsonify(result)

# ------------------ Purchases List ------------------
@token_required
@reports_bp.route('/purchases-list', methods=['GET'])
def purchases_list():
    purchases = db.session.query(PurchaseOrder).filter(PurchaseOrder.status != 9).all()
    result = [{
        "id": p.id,
        "product_name": p.product.name if p.product else "N/A",
        "quantity": p.quantity,
        "total_amount": float(p.total_amount),
        "purchase_date": p.purchase_date.strftime('%Y-%m-%d')
    } for p in purchases]
    return jsonify(result)

# ------------------ Expenses Report ------------------
@token_required
@reports_bp.route('/expenses-report', methods=['GET'])
def expenses_report():
    expenses = db.session.query(Expense).filter(Expense.status != 9).all()
    result = [{
        "id": e.id,
        "description": e.description,
        "amount": float(e.total_amount),
        "expense_date": e.expense_date.strftime('%Y-%m-%d')
    } for e in expenses]
    return jsonify(result)

@token_required
@reports_bp.route('/profit-loss-professional', methods=['GET'])
def profit_loss_professional():
    """
    Returns a professional, nested Profit & Loss report.
    Revenue → COGS (id=30) → Other Expenses → Net Profit
    Supports date filtering with start_date and end_date query params.
    """
    # ------------------ Date filters ------------------
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    filters = [GeneralLedger.status != 9]

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            filters.append(GeneralLedger.transaction_date >= start_date)
        except ValueError:
            return jsonify({"error": "start_date must be YYYY-MM-DD"}), 400
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            filters.append(GeneralLedger.transaction_date <= end_date)
        except ValueError:
            return jsonify({"error": "end_date must be YYYY-MM-DD"}), 400

    # ------------------ Fetch accounts with balances ------------------
    accounts = db.session.query(
        Account.id,
        Account.name,
        Account.account_type,
        Account.account_subtype,
        Account.parent_id,
        func.coalesce(func.sum(GeneralLedger.amount), 0).label('balance')
    ).outerjoin(GeneralLedger, GeneralLedger.account_id == Account.id) \
     .filter(Account.status != 9,
             Account.account_type.in_([AccountTypeEnum.REVENUE, AccountTypeEnum.EXPENSE]),
             *filters) \
     .group_by(Account.id).all()

    # ------------------ Build account dict ------------------
    account_dict = {}
    for a in accounts:
        account_dict[a.id] = {
            "id": a.id,
            "name": a.name,
            "type": a.account_type.value if hasattr(a.account_type, 'value') else str(a.account_type),
            "subtype": a.account_subtype.value if hasattr(a.account_subtype, 'value') else str(a.account_subtype),
            "balance": float(a.balance),
            "children": [],
            "parent_id": a.parent_id
        }

    # ------------------ Build hierarchy ------------------
    root_accounts = []
    for acc in account_dict.values():
        if acc["parent_id"] and acc["parent_id"] in account_dict:
            account_dict[acc["parent_id"]]["children"].append(acc)
        elif acc["parent_id"] is None:
            root_accounts.append(acc)

    # ------------------ Recursive sum function ------------------
    def sum_children(account):
        for child in account["children"]:
            account["balance"] += sum_children(child)
        return account["balance"]

    for root in root_accounts:
        sum_children(root)

    # ------------------ Separate Revenue, COGS (id=30), Expenses ------------------
    revenue_accounts = []
    cogs_account = account_dict.get(30)  # COGS hardcoded
    expense_accounts = []

    for acc in root_accounts:
        if acc["type"] == "REVENUE" and acc["id"] != 30:
            revenue_accounts.append(acc)
        elif acc["type"] == "EXPENSE":
            expense_accounts.append(acc)

    total_revenue = sum(a["balance"] for a in revenue_accounts)
    total_cogs = cogs_account["balance"] if cogs_account else 0
    total_expenses = sum(a["balance"] for a in expense_accounts)
    net_profit = total_revenue - total_cogs - total_expenses

    # ------------------ Build final ordered list ------------------
    final_accounts = revenue_accounts[:]
    if cogs_account:
        final_accounts.append(cogs_account)  # COGS after revenue
    final_accounts.extend(expense_accounts)  # then other expenses

    # ------------------ Response ------------------
    return jsonify({
        "period": {
            "start_date": start_date_str if start_date_str else None,
            "end_date": end_date_str if end_date_str else None
        },
        "accounts": final_accounts,
        "totals": {
            "total_revenue": total_revenue,
            "total_cogs": total_cogs,
            "total_expenses": total_expenses,
            "net_profit": net_profit
        }
    })


@token_required
@reports_bp.route('/profit-loss-periodic', methods=['GET'])
def profit_loss_periodic():
    """
    Returns a professional-style Profit & Loss report grouped by month.
    Layout:
      Revenue → COGS (id=30) → Other Expenses → Net Profit
    Supports start_date and end_date filters.
    """
    from sqlalchemy import extract
    from collections import defaultdict

    # ------------------ Date filters ------------------
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    filters = [GeneralLedger.status != 9]

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            filters.append(GeneralLedger.transaction_date >= start_date)
        except ValueError:
            return jsonify({"error": "start_date must be YYYY-MM-DD"}), 400
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            filters.append(GeneralLedger.transaction_date <= end_date)
        except ValueError:
            return jsonify({"error": "end_date must be YYYY-MM-DD"}), 400

    # ------------------ Fetch account balances grouped by month ------------------
    records = db.session.query(
        Account.id.label('account_id'),
        Account.name.label('account_name'),
        Account.account_type,
        Account.account_subtype,
        Account.parent_id,
        extract('year', GeneralLedger.transaction_date).label('year'),
        extract('month', GeneralLedger.transaction_date).label('month'),
        func.coalesce(func.sum(GeneralLedger.amount), 0).label('balance')
    ).outerjoin(GeneralLedger, GeneralLedger.account_id == Account.id) \
     .filter(Account.status != 9,
             Account.account_type.in_([AccountTypeEnum.REVENUE, AccountTypeEnum.EXPENSE]),
             *filters) \
     .group_by(Account.id, extract('year', GeneralLedger.transaction_date), extract('month', GeneralLedger.transaction_date)) \
     .order_by('year', 'month').all()

    monthly_data = defaultdict(list)

    for r in records:
        period = f"{int(r.year)}-{int(r.month):02d}" if r.year and r.month else "Unknown"
        monthly_data[period].append({
            "id": r.account_id,
            "name": r.account_name,
            "type": r.account_type.value if hasattr(r.account_type, 'value') else str(r.account_type),
            "subtype": r.account_subtype.value if hasattr(r.account_subtype, 'value') else str(r.account_subtype),
            "balance": float(r.balance),
            "children": [],
            "parent_id": r.parent_id
        })

    # ------------------ Build hierarchy + professional grouping ------------------
    def build_hierarchy(accounts):
        acc_map = {a["id"]: dict(a, children=[]) for a in accounts}
        roots = []
        for acc in acc_map.values():
            if acc["parent_id"] and acc["parent_id"] in acc_map:
                acc_map[acc["parent_id"]]["children"].append(acc)
            else:
                roots.append(acc)

        def sum_children(acc):
            for child in acc["children"]:
                acc["balance"] += sum_children(child)
            return acc["balance"]

        for root in roots:
            sum_children(root)
        return roots

    # ------------------ Compute professional layout per period ------------------
    final_response = {}
    for period, accounts in monthly_data.items():
        hierarchy = build_hierarchy(accounts)

        account_dict = {a["id"]: a for a in accounts}
        cogs_account = account_dict.get(30)  # hardcoded COGS id=30

        revenue_accounts = [a for a in hierarchy if a["type"] == "REVENUE" and a["id"] != 30]
        expense_accounts = [a for a in hierarchy if a["type"] == "EXPENSE"]

        total_revenue = sum(a["balance"] for a in revenue_accounts)
        total_cogs = cogs_account["balance"] if cogs_account else 0
        total_expenses = sum(a["balance"] for a in expense_accounts)
        net_profit = total_revenue - total_cogs - total_expenses

        final_accounts = revenue_accounts[:]
        if cogs_account:
            final_accounts.append(cogs_account)
        final_accounts.extend(expense_accounts)

        final_response[period] = {
            "accounts": final_accounts,
            "totals": {
                "total_revenue": round(total_revenue, 2),
                "total_cogs": round(total_cogs, 2),
                "total_expenses": round(total_expenses, 2),
                "net_profit": round(net_profit, 2)
            }
        }

    return jsonify({
        "period_filter": {
            "start_date": start_date_str or None,
            "end_date": end_date_str or None
        },
        "data": final_response
    })

@token_required
@reports_bp.route('/profit-loss-ytd', methods=['GET'])
def profit_loss_ytd():
    """
    Returns a professional-style Profit & Loss report grouped by year and month.
    Layout:
      Revenue → COGS (id=30) → Other Expenses → Net Profit → YTD Profit
    """
    from sqlalchemy import extract
    from collections import defaultdict

    # ------------------ Date filters ------------------
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    filters = [GeneralLedger.status != 9]

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            filters.append(GeneralLedger.transaction_date >= start_date)
        except ValueError:
            return jsonify({"error": "start_date must be YYYY-MM-DD"}), 400
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            filters.append(GeneralLedger.transaction_date <= end_date)
        except ValueError:
            return jsonify({"error": "end_date must be YYYY-MM-DD"}), 400

    # ------------------ Fetch balances grouped by month ------------------
    records = db.session.query(
        Account.id.label('account_id'),
        Account.name.label('account_name'),
        Account.account_type,
        Account.account_subtype,
        Account.parent_id,
        extract('year', GeneralLedger.transaction_date).label('year'),
        extract('month', GeneralLedger.transaction_date).label('month'),
        func.coalesce(func.sum(GeneralLedger.amount), 0).label('balance')
    ).outerjoin(GeneralLedger, GeneralLedger.account_id == Account.id) \
     .filter(Account.status != 9,
             Account.account_type.in_([AccountTypeEnum.REVENUE, AccountTypeEnum.EXPENSE]),
             *filters) \
     .group_by(Account.id, extract('year', GeneralLedger.transaction_date), extract('month', GeneralLedger.transaction_date)) \
     .order_by('year', 'month').all()

    monthly_data = defaultdict(list)
    for r in records:
        period = f"{int(r.year)}-{int(r.month):02d}" if r.year and r.month else "Unknown"
        monthly_data[period].append({
            "id": r.account_id,
            "name": r.account_name,
            "type": r.account_type.value if hasattr(r.account_type, 'value') else str(r.account_type),
            "subtype": r.account_subtype.value if hasattr(r.account_subtype, 'value') else str(r.account_subtype),
            "balance": float(r.balance),
            "children": [],
            "parent_id": r.parent_id
        })

    # ------------------ Build hierarchy and professional grouping ------------------
    def build_hierarchy(accounts):
        acc_map = {a["id"]: dict(a, children=[]) for a in accounts}
        roots = []
        for acc in acc_map.values():
            if acc["parent_id"] and acc["parent_id"] in acc_map:
                acc_map[acc["parent_id"]]["children"].append(acc)
            else:
                roots.append(acc)

        def sum_children(acc):
            for child in acc["children"]:
                acc["balance"] += sum_children(child)
            return acc["balance"]

        for root in roots:
            sum_children(root)
        return roots

    final_response = {}
    annual_totals = defaultdict(lambda: {"total_revenue": 0, "total_cogs": 0, "total_expenses": 0, "net_profit": 0})
    ytd_totals = defaultdict(lambda: 0.0)

    for period in sorted(monthly_data.keys()):
        hierarchy = build_hierarchy(monthly_data[period])
        account_dict = {a["id"]: a for a in monthly_data[period]}
        cogs_account = account_dict.get(30)

        revenue_accounts = [a for a in hierarchy if a["type"] == "REVENUE" and a["id"] != 30]
        expense_accounts = [a for a in hierarchy if a["type"] == "EXPENSE"]

        total_revenue = sum(a["balance"] for a in revenue_accounts)
        total_cogs = cogs_account["balance"] if cogs_account else 0
        total_expenses = sum(a["balance"] for a in expense_accounts)
        net_profit = total_revenue - total_cogs - total_expenses

        year = int(period.split("-")[0]) if period != "Unknown" else "Unknown"
        annual_totals[year]["total_revenue"] += total_revenue
        annual_totals[year]["total_cogs"] += total_cogs
        annual_totals[year]["total_expenses"] += total_expenses
        annual_totals[year]["net_profit"] += net_profit
        ytd_totals[year] += net_profit

        final_accounts = revenue_accounts[:]
        if cogs_account:
            final_accounts.append(cogs_account)
        final_accounts.extend(expense_accounts)

        final_response[period] = {
            "accounts": final_accounts,
            "totals": {
                "total_revenue": round(total_revenue, 2),
                "total_cogs": round(total_cogs, 2),
                "total_expenses": round(total_expenses, 2),
                "net_profit": round(net_profit, 2),
                "ytd_profit": round(ytd_totals[year], 2)
            }
        }

    return jsonify({
        "period_filter": {
            "start_date": start_date_str or None,
            "end_date": end_date_str or None
        },
        "monthly_data": final_response,
        "annual_totals": {
            str(y): {k: round(v, 2) for k, v in t.items()}
            for y, t in annual_totals.items()
        }
    })

# ---------------------------------------
@token_required
@reports_bp.route("/balance-sheet", methods=["GET"])
def balance_sheet_report():
    """
    Professional Balance Sheet Report
    ---------------------------------
    - Groups by AccountType (ASSET, LIABILITY, EQUITY)
    - Subtotals by account_subtype
    - Supports ?as_of=YYYY-MM-DD
    - Checks that Assets = Liabilities + Equity
    """

    # --- Date filter ---
    as_of_str = request.args.get("as_of")
    as_of = datetime.strptime(as_of_str, "%Y-%m-%d") if as_of_str else datetime.utcnow()

    # --- CASE expression for proper accounting balances ---
    balance_expr = func.coalesce(
        func.sum(
            case(
                # Assets & Expenses: Debit increases, Credit decreases
                ( (Account.account_type.in_(["ASSET", "EXPENSE"])) & (GeneralLedger.transaction_type == "Debit"), GeneralLedger.amount ),
                ( (Account.account_type.in_(["ASSET", "EXPENSE"])) & (GeneralLedger.transaction_type == "Credit"), -GeneralLedger.amount ),
                # Liabilities, Equity, Revenue: Credit increases, Debit decreases
                ( (Account.account_type.in_(["LIABILITY", "EQUITY", "REVENUE"])) & (GeneralLedger.transaction_type == "Debit"), -GeneralLedger.amount ),
                ( (Account.account_type.in_(["LIABILITY", "EQUITY", "REVENUE"])) & (GeneralLedger.transaction_type == "Credit"), GeneralLedger.amount ),
                else_=0.0
            )
        ),
        0.0
    )

    # --- Base query ---
    query = (
        db.session.query(
            Account.account_type,
            Account.account_subtype,
            Account.id.label("account_id"),
            Account.name.label("account_name"),
            balance_expr.label("balance")
        )
        .outerjoin(GeneralLedger, GeneralLedger.account_id == Account.id)
        .filter(Account.status != 9)
        .group_by(Account.account_type, Account.account_subtype, Account.id, Account.name)
        .order_by(Account.account_type, Account.account_subtype, Account.name)
    )

    results = query.all()

    # --- Organize by sections and subtypes ---
    balance_sheet = {"ASSET": {}, "LIABILITY": {}, "EQUITY": {}}

    for row in results:
        type_key = row.account_type.value  # Enum to string
        subtype_key = row.account_subtype or "Uncategorized"

        if type_key not in balance_sheet:
            continue  # Skip Revenue/Expense

        if subtype_key not in balance_sheet[type_key]:
            balance_sheet[type_key][subtype_key] = []

        balance_sheet[type_key][subtype_key].append({
            "account_id": row.account_id,
            "account_name": row.account_name,
            "balance": float(row.balance)
        })

    # --- Calculate subtotals and totals ---
    totals = {}
    for section, subtypes in balance_sheet.items():
        totals[section] = {"subtotals": {}, "total": 0.0}
        for subtype, accounts in subtypes.items():
            subtotal = round(sum(a["balance"] for a in accounts), 2)
            totals[section]["subtotals"][subtype] = subtotal
            totals[section]["total"] += subtotal
        totals[section]["total"] = round(totals[section]["total"], 2)

    # --- Accounting equation check ---
    total_assets = totals.get("ASSET", {}).get("total", 0.0)
    total_liabilities = totals.get("LIABILITY", {}).get("total", 0.0)
    total_equity = totals.get("EQUITY", {}).get("total", 0.0)
    balance_check = round(total_assets - (total_liabilities + total_equity), 2)

    # --- Final JSON response ---
    return jsonify({
        "as_of": as_of.strftime("%Y-%m-%d"),
        "sections": balance_sheet,
        "totals": totals,
        "summary": {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "assets_minus_liabilities_equity": balance_check,
            "total_liabilities_equity":total_equity+total_liabilities,
            "is_balanced": balance_check == 0
        }
    })
@token_required
@reports_bp.route("/sales", methods=["GET"])
def sales_report():
    """
    Returns sales report for a given date range.
    Includes profit/loss per sale, customer details, category/unit info,
    and indicates outstanding balances.
    Optionally filters by customer_id or category.
    """

    # --- Parse filters ---
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    customer_id = request.args.get("customer_id", type=int)
    category_id = request.args.get("category_id", type=int)

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
    except ValueError:
        return jsonify({"error": "Dates must be in YYYY-MM-DD format"}), 400

    # --- Base filters ---
    filters = [Sale.status != 9]
    if start_date:
        filters.append(Sale.sale_date >= start_date)
    if end_date:
        filters.append(Sale.sale_date <= end_date)
    if customer_id:
        filters.append(Sale.customer_id == customer_id)

    # --- Fetch all sales ---
    sales = (
        db.session.query(Sale)
        .options(joinedload(Sale.items), joinedload(Sale.customer))
        .filter(*filters)
        .order_by(Sale.sale_date.desc())
        .all()
    )

    report_data = []
    total_sales = total_profit = total_balance = total_cost = total_paid = 0

    for sale in sales:
        total_amount = sum(item.total_price for item in sale.items if item.status != 9)
        total_paid_amount = sale.total_paid or 0
        balance = total_amount - total_paid_amount

        total_cost_price = 0
        total_profit_loss = 0
        sale_items_data = []

        for item in sale.items:
            if item.status == 9:
                continue

            product = Product.query.get(item.product_id)
            if not product:
                continue

            # --- Category ---
            category_name = None
            if product.category_id:
                category = db.session.query(Category).filter_by(id=product.category_id, status=1).first()
                if category:
                    category_name = category.name

            # --- Unit info ---
            unit_name = None
            conversion_qty = 1
            is_returnable = False
            if item.unit_id:
                unit = ProductUnit.query.get(item.unit_id)
                if unit:
                    unit_name = unit.unit_name
                    conversion_qty = unit.conversion_quantity or 1
                    is_returnable = unit.is_returnable

            # --- Convert quantity back to base unit if returnable ---
            actual_qty = item.quantity
            if is_returnable:
                actual_qty = item.quantity * conversion_qty

            # --- Get last purchase price ---
            # last_purchase = None
            # is_base_unit = True
            # if item.unit_id:
            # #     # Try to find exact unit purchase before sale date
            #     last_purchase = (
            #         PurchaseOrderItem.query
            #         .filter(
            #             PurchaseOrderItem.product_id == product.id,
            #             PurchaseOrderItem.status == 1,
            #             PurchaseOrderItem.unit_id == item.unit_id,
            #             PurchaseOrderItem.created_at <= (end_date or datetime.utcnow())
            #         )
            #         .order_by(PurchaseOrderItem.created_at.desc())
            #         .first()
            #     )
            # if not last_purchase:

            #     is_base_unit=False

            last_purchase_price, is_base_unit =get_latest_purchase_price_no_rounds(product.id,item.unit_id,end_date)
            print(" last_purchase_price ",last_purchase_price)
            print(" is_base_unit ",is_base_unit)


            unit_cost = round(last_purchase_price, 2) 
            unit_selling = float(item.unit_price or 0)
            profit = (unit_selling - unit_cost) * item.quantity if is_base_unit else  (unit_selling - unit_cost) * actual_qty 
            cost_value = unit_cost * item.quantity if is_base_unit else unit_cost * actual_qty

            total_cost_price += cost_value
            total_profit_loss += profit

            sale_items_data.append({
                "product_id": product.id,
                "product_name": product.name,
                "category": category_name,
                "unit_name": unit_name,
                "quantity": item.quantity,
                "converted_quantity": actual_qty,
                "unit_price": unit_selling,
                "cost_price": unit_cost,
                "total_price": item.total_price,
                "profit": profit
            })

        # --- Customer info ---
        customer_name = sale.customer.name if sale.customer else "Walk-in Customer"
        customer_phone = getattr(sale.customer, "phone", "")

        sale_entry = {
            "sale_id": sale.id,
            "sale_number": sale.sale_number,
            "sale_date": sale.sale_date.strftime("%Y-%m-%d"),
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "total_amount": round(total_amount, 2),
            "total_cost": round(total_cost_price, 2),
            "profit_loss": round(total_profit_loss, 2),
            "amount_paid": round(total_paid_amount, 2),
            "balance": round(balance, 2),
            "status": sale.payment_status,
            "items": sale_items_data
        }

        # --- Category filter ---
        if category_id:
            if not any(
                Product.query.get(i["product_id"]).category_id == category_id for i in sale_items_data
            ):
                continue

        report_data.append(sale_entry)

        total_sales += total_amount
        total_profit += total_profit_loss
        total_balance += balance
        total_cost += total_cost_price
        total_paid += total_paid_amount

    summary = {
        "total_sales": round(total_sales, 2),
        "total_cost": round(total_cost, 2),
        "total_profit_loss": round(total_profit, 2),
        "total_paid": round(total_paid, 2),
        "total_balance": round(total_balance, 2),
    }

    return jsonify({
        "period": {
            "start_date": start_date_str,
            "end_date": end_date_str
        },
        "sales_count": len(report_data),
        "summary": summary,
        "data": report_data
    })


# @token_required
# @reports_bp.route("/sales", methods=["GET"])
# def sales_report():
#     """
#     Returns sales report for a given date range.
#     Includes profit/loss per sale, customer details, category/unit info,
#     and indicates outstanding balances.
#     Optionally filters by customer_id or category.
#     """

#     # --- Parse filters ---
#     start_date_str = request.args.get("start_date")
#     end_date_str = request.args.get("end_date")
#     customer_id = request.args.get("customer_id", type=int)
#     category_id = request.args.get("category_id", type=int)

#     try:
#         start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
#         end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
#     except ValueError:
#         return jsonify({"error": "Dates must be in YYYY-MM-DD format"}), 400

#     # --- Base filters ---
#     filters = [Sale.status != 9]
#     if start_date:
#         filters.append(Sale.sale_date >= start_date)
#     if end_date:
#         filters.append(Sale.sale_date <= end_date)
#     if customer_id:
#         filters.append(Sale.customer_id == customer_id)

#     # --- Fetch all sales ---
#     sales = (
#         db.session.query(Sale)
#         .options(joinedload(Sale.items), joinedload(Sale.customer))
#         .filter(*filters)
#         .order_by(Sale.sale_date.desc())
#         .all()
#     )

#     report_data = []
#     total_sales = total_profit = total_balance = total_cost = total_paid = 0

#     for sale in sales:
#         # --- Compute totals ---
#         total_amount = sum(item.total_price for item in sale.items if item.status != 9)
#         total_paid_amount = sale.total_paid or 0
#         balance = total_amount - total_paid_amount

#         total_cost_price = 0
#         total_profit_loss = 0
#         sale_items_data = []

#         for item in sale.items:
#             if item.status == 9:
#                 continue

#             product = Product.query.get(item.product_id)
#             if not product:
#                 continue

#             category_name = None
#             if product.category_id:
#                 category = db.session.query(Category).filter_by(id=product.category_id, status=1).first()
#                 if category:
#                     category_name = category.name

#             # --- Get product unit info ---
#             unit_name = None
#             conversion_qty = 1
#             is_returnable = False
#             if item.unit_id:
#                 unit = ProductUnit.query.get(item.unit_id)
#                 if unit:
#                     unit_name = unit.unit_name
#                     conversion_qty = unit.conversion_quantity or 1
#                     is_returnable = unit.is_returnable  # Assuming you have this column

#             # --- Convert quantity back to base unit if returnable ---
#             actual_qty = item.quantity
#             if is_returnable:
#                 actual_qty = item.quantity * conversion_qty
            
#             # --- Get last purchase price for this product/unit ---
#             last_purchase = (
#                 PurchaseOrderItem.query
#                 .filter(
#                     PurchaseOrderItem.product_id == product.id,
#                     PurchaseOrderItem.status == 1,
#                     # Optional: filter by unit_id if needed
#                     PurchaseOrderItem.unit_id == item.unit_id if item.unit_id else True
#                 )
#                 .order_by(PurchaseOrderItem.created_at.desc())
#                 .first()
#             )
#             last_purchase_price = float(last_purchase.unit_price or 0) if last_purchase else 0

#             # last_purchase_price= last_purchase_price/conversion_qty


#             # last_purchase_price = last_purchase.unit_price if last_purchase else 0
            

#             unit_cost = round(last_purchase_price or 0)
            
#             unit_selling = float(item.unit_price or 0)

#             profit = (unit_selling - unit_cost) * actual_qty
#             cost_value = unit_cost * actual_qty

#             total_cost_price += cost_value
#             total_profit_loss += profit

#             sale_items_data.append({
#                 "product_id": product.id,
#                 "product_name": product.name,
#                 "category": category_name,
#                 "unit_name": unit_name,
#                 "quantity": item.quantity,
#                 "converted_quantity": actual_qty,
#                 "unit_price": unit_selling,
#                 "cost_price": unit_cost,
#                 "total_price": item.total_price,
#                 "profit": profit
#             })

#         # --- Customer info ---
#         customer_name = sale.customer.name if sale.customer else "Walk-in Customer"
#         customer_phone = getattr(sale.customer, "phone", "")

#         # --- Prepare sale entry ---
#         sale_entry = {
#             "sale_id": sale.id,
#             "sale_number": sale.sale_number,
#             "sale_date": sale.sale_date.strftime("%Y-%m-%d"),
#             "customer_name": customer_name,
#             "customer_phone": customer_phone,
#             "total_amount": round(total_amount, 2),
#             "total_cost": round(total_cost_price, 2),
#             "profit_loss": round(total_profit_loss, 2),
#             "amount_paid": round(total_paid_amount, 2),
#             "balance": round(balance, 2),
#             "status": sale.payment_status,
#             "items": sale_items_data
#         }

#         # Optional filter by category (post-filter)
#         if category_id:
#             if not any(
#                 Product.query.get(i["product_id"]).category_id == category_id for i in sale_items_data
#             ):
#                 continue

#         report_data.append(sale_entry)

#         # --- Accumulate totals ---
#         total_sales += total_amount
#         total_profit += total_profit_loss
#         total_balance += balance
#         total_cost += total_cost_price
#         total_paid += total_paid_amount

#     # --- Summary totals ---
#     summary = {
#         "total_sales": round(total_sales, 2),
#         "total_cost": round(total_cost, 2),
#         "total_profit_loss": round(total_profit, 2),
#         "total_paid": round(total_paid, 2),
#         "total_balance": round(total_balance, 2),
#     }

#     return jsonify({
#         "period": {
#             "start_date": start_date_str,
#             "end_date": end_date_str
#         },
#         "sales_count": len(report_data),
#         "summary": summary,
#         "data": report_data
#     })



@token_required
@reports_bp.route("/sales-profit-loss", methods=["GET"])
def sales_profit_loss():
    """
    Returns aggregated Profit & Loss report over a period.
    Summarizes total sales, total cost, total profit/loss, and balances.
    Optionally filtered by customer_id or category_id.
    """

    # --- Parse filters ---
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    customer_id = request.args.get("customer_id", type=int)
    category_id = request.args.get("category_id", type=int)

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
    except ValueError:
        return jsonify({"error": "Dates must be in YYYY-MM-DD format"}), 400

    # --- Base filters ---
    filters = [Sale.status != 9]
    if start_date:
        filters.append(Sale.sale_date >= start_date)
    if end_date:
        filters.append(Sale.sale_date <= end_date)
    if customer_id:
        filters.append(Sale.customer_id == customer_id)

    # --- Fetch sales ---
    sales = (
        db.session.query(Sale)
        .options(joinedload(Sale.items), joinedload(Sale.customer))
        .filter(*filters)
        .order_by(Sale.sale_date.desc())
        .all()
    )

    # --- Initialize totals ---
    total_sales = total_cost = total_profit = total_balance = total_paid = 0
    report_items = []

    for sale in sales:
        sale_total_amount = 0
        sale_total_cost = 0
        sale_total_profit = 0
        sale_balance = 0

        for item in sale.items:
            if item.status == 9:
                continue

            product = Product.query.get(item.product_id)
            if not product:
                continue

            # Optional category filter
            if category_id and product.category_id != category_id:
                continue

            # --- Product unit info ---
            conversion_qty = 1
            is_returnable = False
            if item.unit_id:
                unit = ProductUnit.query.get(item.unit_id)
                if unit:
                    conversion_qty = unit.conversion_qty or 1
                    is_returnable = unit.is_returnable

            # --- Adjust quantity ---
            actual_qty = item.quantity
            if is_returnable and conversion_qty > 1:
                actual_qty = item.quantity * conversion_qty

            # # --- Last purchase price ---
            # last_purchase = (
            #     PurchaseOrderItem.query
            #     .filter(
            #         PurchaseOrderItem.product_id == product.id,
            #         PurchaseOrderItem.status == 1,
            #         PurchaseOrderItem.unit_id == item.unit_id if item.unit_id else True
            #     )
            #     .order_by(PurchaseOrderItem.created_at.desc())
            #     .first()
            # )
            # last_purchase_price = float(last_purchase.unit_price or 0) if last_purchase else 0
            # last_purchase_price = last_purchase_price / conversion_qty if conversion_qty > 1 else last_purchase_price
            last_purchase_price=get_latest_purchase_price(product.id,item.unit_id ,end_date)


            # --- Cost & Profit ---
            unit_selling = float(item.unit_price or 0)
            cost_value = last_purchase_price * actual_qty
            profit_value = (unit_selling - last_purchase_price) * actual_qty

            sale_total_amount += item.total_price
            sale_total_cost += cost_value
            sale_total_profit += profit_value

        sale_total_paid = sale.total_paid or 0
        sale_balance = sale_total_amount - sale_total_paid

        total_sales += sale_total_amount
        total_cost += sale_total_cost
        total_profit += sale_total_profit
        total_paid += sale_total_paid
        total_balance += sale_balance

        # Record per-sale summary
        report_items.append({
            "sale_id": sale.id,
            "sale_number": sale.sale_number,
            "sale_date": sale.sale_date.strftime("%Y-%m-%d"),
            "customer": sale.customer.name if sale.customer else "Walk-in",
            "total_sales": round(sale_total_amount, 2),
            "total_cost": round(sale_total_cost, 2),
            "profit_loss": round(sale_total_profit, 2),
            "amount_paid": round(sale_total_paid, 2),
            "balance": round(sale_balance, 2)
        })

    # --- Final summary ---
    summary = {
        "total_sales": round(total_sales, 2),
        "total_cost": round(total_cost, 2),
        "total_profit_loss": round(total_profit, 2),
        "total_paid": round(total_paid, 2),
        "total_balance": round(total_balance, 2)
    }

    return jsonify({
        "period": {"start_date": start_date_str, "end_date": end_date_str},
        "sales_count": len(report_items),
        "summary": summary,
        "sales": report_items
    })





from sqlalchemy.orm import joinedload


@token_required
@reports_bp.route("/products_purhcased", methods=["GET"])
def get_pruchased_products():
    search = request.args.get("search")
    return {"data":get_purchase_orders(search)}

def get_purchase_orders(search=None):
    """
    Returns a list of purchase orders with details including product, unit, supplier, category, and quantities.
    Supports search by product name, invoice number, or supplier name.
    
    Args:
        search (str, optional): Search term to filter by product name, invoice number, or supplier name.
    
    Returns:
        list of dict: Each dict contains purchase order details and product/unit info.
    """

    # Base query: eager load supplier, items, product, unit, and product category
    query = PurchaseOrder.query.options(
        joinedload(PurchaseOrder.supplier),
        joinedload(PurchaseOrder.items)
            .joinedload(PurchaseOrderItem.product)
            .joinedload(Product.category),
        joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.unit)
    )

    # Apply search filter if given
    if search:
        search_term = f"%{search}%"
        query = query.join(PurchaseOrder.supplier)\
                     .join(PurchaseOrder.items)\
                     .join(PurchaseOrderItem.product)\
                     .filter(
            db.or_(
                Product.name.ilike(search_term),
                PurchaseOrder.invoice_number.ilike(search_term),
                Supplier.name.ilike(search_term)
            )
        )

    # Order by most recent purchases
    query = query.order_by(PurchaseOrder.purchase_date.desc())

    results = []

    for po in query.all():
        po_data = {
            "purchase_order_id": po.id,
            "invoice_number": po.invoice_number,
            "supplier_name": po.supplier.name,
            "purchase_date": po.purchase_date.strftime("%Y-%m-%d %H:%M:%S") if po.purchase_date else None,
            "total_amount": po.total_amount,
            "total_paid": po.total_paid,
            "total_balance": po.total_balance,
            "items": []
        }

        for item in po.items:
            # Skip inactive items
            if item.status != 1:
                continue

            unit_name = item.unit.unit_name if item.unit else "Base"
            conversion_qty = item.unit.conversion_quantity if item.unit else 1
            converted_qty = item.quantity * conversion_qty

            category_name = item.product.category.name if item.product and item.product.category_id else None

            item_data = {
                "product_name": item.product.name if item.product else None,
                "product_id": item.product_id,
                "category_name": category_name,
                "unit_name": unit_name,
                "conversion_quantity": conversion_qty,
                "quantity_purchased": item.quantity,
                "converted_quantity": converted_qty,
                "unit_price": item.unit_price,
                "total_price": item.total_price
            }

            po_data["items"].append(item_data)

        results.append(po_data)

    return results

