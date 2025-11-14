# from flask import Blueprint, jsonify, request
# from app import db
# from app.models import Product, Sale, SaleItem, Expense, Customer, Supplier, PurchaseOrder
# from sqlalchemy import func
# from datetime import datetime, timedelta

# from app.utils.auth import token_required

# dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


# def parse_date_range(period, start_date_str=None, end_date_str=None):
#     today = datetime.utcnow().date()
    
#     if period == 'today':
#         start_date = end_date = today
#     elif period == 'week':
#         start_date = today - timedelta(days=today.weekday())  # Monday
#         end_date = start_date + timedelta(days=6)            # Sunday
#     elif period == 'month':
#         start_date = today.replace(day=1)
#         # Last day of the month
#         next_month = start_date.replace(day=28) + timedelta(days=4)
#         end_date = next_month - timedelta(days=next_month.day)
#     elif period == 'custom' and start_date_str and end_date_str:
#         start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#         end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
#     else:
#         # default to today if invalid
#         start_date = end_date = today
    
#     return start_date, end_date


# @token_required
# @dashboard_bp.route('/metrics', methods=['GET'])
# def get_dashboard_metrics():
#     # ------------------ Period Filter ------------------
#     period = request.args.get('period', 'today')  # today, week, month, custom
#     start_date_str = request.args.get('start_date')
#     end_date_str = request.args.get('end_date')
    
#     start_date, end_date = parse_date_range(period, start_date_str, end_date_str)
    
#     # ------------------ Last 7 Days for Charts ------------------
#     today = datetime.utcnow().date()
#     seven_days_ago = today - timedelta(days=6)
#     days_list = [(seven_days_ago + timedelta(days=i)) for i in range(7)]

#     # ------------------ Totals ------------------
#     total_products = db.session.query(func.count(Product.id)).filter(Product.status != 9).scalar()
#     total_sales = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(Sale.status != 9).scalar()
#     total_expenses = db.session.query(func.coalesce(func.sum(Expense.total_amount), 0)).filter(Expense.status != 9).scalar()
#     total_customers = db.session.query(func.count(Customer.id)).filter(Customer.status != 9).scalar()
#     total_suppliers = db.session.query(func.count(Supplier.id)).filter(Supplier.status != 9).scalar()
#     total_purchase_orders = db.session.query(func.count(PurchaseOrder.id)).filter(PurchaseOrder.status != 9).scalar()

#     # ------------------ Outstanding Balances ------------------
#     outstanding_sales = db.session.query(func.coalesce(func.sum(Sale.balance), 0)).filter(Sale.status != 9).scalar()
#     outstanding_po = db.session.query(func.coalesce(func.sum(PurchaseOrder.total_balance), 0)).filter(PurchaseOrder.status != 9).scalar()

#     # ------------------ Sales & Expenses Last 7 Days ------------------
#     sales_data = dict(
#         db.session.query(
#             func.date(Sale.sale_date).label('day'),
#             func.coalesce(func.sum(Sale.total_amount), 0)
#         )
#         .filter(Sale.status != 9, func.date(Sale.sale_date) >= seven_days_ago)
#         .group_by(func.date(Sale.sale_date))
#         .all()
#     )
#     sales_last_7_days = [{'day': day.strftime('%a'), 'amount': float(sales_data.get(day, 0))} for day in days_list]

#     expenses_data = dict(
#         db.session.query(
#             func.date(Expense.expense_date).label('day'),
#             func.coalesce(func.sum(Expense.total_amount), 0)
#         )
#         .filter(Expense.status != 9, func.date(Expense.expense_date) >= seven_days_ago)
#         .group_by(func.date(Expense.expense_date))
#         .all()
#     )
#     expenses_last_7_days = [{'day': day.strftime('%a'), 'amount': float(expenses_data.get(day, 0))} for day in days_list]

#     # ------------------ Best & Least Products for Selected Period ------------------
#     best_products_query = (
#         db.session.query(SaleItem.product_id, func.coalesce(func.sum(SaleItem.total_price), 0).label('total_revenue'))
#         .join(Sale)
#         .filter(Sale.status != 9, SaleItem.status != 9, func.date(Sale.sale_date) >= start_date, func.date(Sale.sale_date) <= end_date)
#         .group_by(SaleItem.product_id)
#         .order_by(func.sum(SaleItem.total_price).desc())
#         .limit(5)
#         .all()
#     )
#     best_products = [{'product_id': p.product_id,
#                       'product_name': db.session.query(Product.name).filter(Product.id == p.product_id).scalar(),
#                       'total_revenue': float(p.total_revenue)} for p in best_products_query]

#     least_products_query = (
#         db.session.query(SaleItem.product_id, func.coalesce(func.sum(SaleItem.total_price), 0).label('total_revenue'))
#         .join(Sale)
#         .filter(Sale.status != 9, SaleItem.status != 9, func.date(Sale.sale_date) >= start_date, func.date(Sale.sale_date) <= end_date)
#         .group_by(SaleItem.product_id)
#         .order_by(func.sum(SaleItem.total_price).asc())
#         .limit(5)
#         .all()
#     )
#     least_products = [{'product_id': p.product_id,
#                        'product_name': db.session.query(Product.name).filter(Product.id == p.product_id).scalar(),
#                        'total_revenue': float(p.total_revenue)} for p in least_products_query]

#     # ------------------ Metrics for Selected Period ------------------
#     sales_in_range = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
#         Sale.status != 9,
#         func.date(Sale.sale_date) >= start_date,
#         func.date(Sale.sale_date) <= end_date
#     ).scalar()

#     expenses_in_range = db.session.query(func.coalesce(func.sum(Expense.total_amount), 0)).filter(
#         Expense.status != 9,
#         func.date(Expense.expense_date) >= start_date,
#         func.date(Expense.expense_date) <= end_date
#     ).scalar()

#     number_of_sales = db.session.query(func.count(Sale.id)).filter(
#         Sale.status != 9,
#         func.date(Sale.sale_date) >= start_date,
#         func.date(Sale.sale_date) <= end_date
#     ).scalar()

#     number_of_customers = db.session.query(func.count(func.distinct(Sale.customer_id))).filter(
#         Sale.status != 9,
#         func.date(Sale.sale_date) >= start_date,
#         func.date(Sale.sale_date) <= end_date
#     ).scalar()

#     profit_in_range = float(sales_in_range - expenses_in_range)

#     number_of_expenses = db.session.query(func.count(Expense.id)).filter(
#         Expense.status != 9,
#         func.date(Expense.expense_date) >= start_date,
#         func.date(Expense.expense_date) <= end_date
#     ).scalar()

#     return jsonify({
#         "period": period,
#         "startDate": start_date.isoformat(),
#         "endDate": end_date.isoformat(),
#         "totalProducts": total_products,
#         "totalSales": float(total_sales),
#         "totalExpenses": float(total_expenses),
#         "totalCustomers": total_customers,
#         "totalSuppliers": total_suppliers,
#         "totalPurchaseOrders": total_purchase_orders,
#         "outstandingSales": float(outstanding_sales),
#         "outstandingPO": float(outstanding_po),
#         "salesLast7Days": sales_last_7_days,
#         "expensesLast7Days": expenses_last_7_days,
#         "bestPerformingProducts": best_products,
#         "leastPerformingProducts": least_products,
#         "salesInRange": float(sales_in_range),
#         "expensesInRange": float(expenses_in_range),
#         "profitInRange": profit_in_range,
#         "numberOfSales": number_of_sales,
#         "numberOfCustomers": number_of_customers,
#         "numberOfExpenses": number_of_expenses
#     })
from flask import Blueprint, jsonify, request
from app import db
from app.models import Product, Sale, SaleItem, Expense, Customer, Supplier, PurchaseOrder
from sqlalchemy import func
from datetime import datetime, timedelta
from app.utils.auth import token_required
from app.utils.gl_utils import get_latest_purchase_price, get_latest_purchase_price_no_rounds

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def parse_date_range(period, start_date_str=None, end_date_str=None):
    today = datetime.utcnow().date()
    
    if period == 'today':
        start_date = end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
    elif period == 'custom' and start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        start_date = end_date = today
    
    return start_date, end_date


@token_required
@dashboard_bp.route('/metrics', methods=['GET'])
def get_dashboard_metrics():
    period = request.args.get('period', 'today')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date, end_date = parse_date_range(period, start_date_str, end_date_str)
    
    today = datetime.utcnow().date()
    seven_days_ago = today - timedelta(days=6)
    days_list = [(seven_days_ago + timedelta(days=i)) for i in range(7)]

    # ------------------ Totals ------------------
    total_products = db.session.query(func.count(Product.id)).filter(Product.status != 9).scalar()
    total_customers = db.session.query(func.count(Customer.id)).filter(Customer.status != 9).scalar()
    total_suppliers = db.session.query(func.count(Supplier.id)).filter(Supplier.status != 9).scalar()
    total_purchase_orders = db.session.query(func.count(PurchaseOrder.id)).filter(PurchaseOrder.status != 9).scalar()

    total_sales = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0))\
        .filter(Sale.status != 9,
                func.date(Sale.sale_date) >= start_date,
                func.date(Sale.sale_date) <= end_date).scalar()

    total_expenses = db.session.query(func.coalesce(func.sum(Expense.total_amount), 0))\
        .filter(Expense.status != 9,
                func.date(Expense.expense_date) >= start_date,
                func.date(Expense.expense_date) <= end_date).scalar()

    # ------------------ Outstanding Balances ------------------
    outstanding_sales = db.session.query(func.coalesce(func.sum(Sale.balance), 0))\
        .filter(Sale.status != 9).scalar()

    outstanding_po = db.session.query(func.coalesce(func.sum(PurchaseOrder.total_balance), 0))\
        .filter(PurchaseOrder.status != 9).scalar()

    # ------------------ Sales & Expenses Last 7 Days ------------------
    sales_data = dict(
        db.session.query(
            func.date(Sale.sale_date).label('day'),
            func.coalesce(func.sum(Sale.total_amount), 0)
        )
        .filter(Sale.status != 9, func.date(Sale.sale_date) >= seven_days_ago)
        .group_by(func.date(Sale.sale_date))
        .all()
    )
    sales_last_7_days = [{'day': day.strftime('%a'), 'amount': float(sales_data.get(day, 0))} for day in days_list]

    expenses_data = dict(
        db.session.query(
            func.date(Expense.expense_date).label('day'),
            func.coalesce(func.sum(Expense.total_amount), 0)
        )
        .filter(Expense.status != 9, func.date(Expense.expense_date) >= seven_days_ago)
        .group_by(func.date(Expense.expense_date))
        .all()
    )
    expenses_last_7_days = [{'day': day.strftime('%a'), 'amount': float(expenses_data.get(day, 0))} for day in days_list]

    # ------------------ Best & Least Products for Selected Period ------------------
    best_products_query = (
        db.session.query(SaleItem.product_id, func.coalesce(func.sum(SaleItem.total_price), 0).label('total_revenue'))
        .join(Sale)
        .filter(Sale.status != 9, SaleItem.status != 9,
                func.date(Sale.sale_date) >= start_date,
                func.date(Sale.sale_date) <= end_date)
        .group_by(SaleItem.product_id)
        .order_by(func.sum(SaleItem.total_price).desc())
        .limit(5)
        .all()
    )
    best_products = [{'product_id': p.product_id,
                      'product_name': db.session.query(Product.name).filter(Product.id == p.product_id).scalar(),
                      'total_revenue': float(p.total_revenue)} for p in best_products_query]

    least_products_query = (
        db.session.query(SaleItem.product_id, func.coalesce(func.sum(SaleItem.total_price), 0).label('total_revenue'))
        .join(Sale)
        .filter(Sale.status != 9, SaleItem.status != 9,
                func.date(Sale.sale_date) >= start_date,
                func.date(Sale.sale_date) <= end_date)
        .group_by(SaleItem.product_id)
        .order_by(func.sum(SaleItem.total_price).asc())
        .limit(5)
        .all()
    )
    least_products = [{'product_id': p.product_id,
                       'product_name': db.session.query(Product.name).filter(Product.id == p.product_id).scalar(),
                       'total_revenue': float(p.total_revenue)} for p in least_products_query]

    # ------------------ Sales Profit ------------------
    sales_items = db.session.query(SaleItem, Sale.sale_date)\
        .join(Sale)\
        .filter(Sale.status != 9, SaleItem.status != 9,
                func.date(Sale.sale_date) >= start_date,
                func.date(Sale.sale_date) <= end_date)\
        .all()

    total_profit = 0
    for item, sale_date in sales_items:
        product = Product.query.get(item.product_id)
        if not product:
            continue

        last_purchase_price, is_base_unit = get_latest_purchase_price_no_rounds(product.id, item.unit_id, sale_date)
        actual_qty = item.quantity
        if item.unit_id and not is_base_unit:
            unit = getattr(product, 'units', None)
            conversion_qty = getattr(unit, 'conversion_quantity', 1)
            actual_qty *= conversion_qty

        unit_cost = float(last_purchase_price or 0)
        unit_selling = float(item.unit_price or 0)
        profit = (unit_selling - unit_cost) * actual_qty
        total_profit += profit

    # ------------------ Profit In Range ------------------
    profit_in_range = round(total_profit - total_expenses, 2)

    # ------------------ Number of Sales & Expenses ------------------
    number_of_sales = db.session.query(func.count(Sale.id))\
        .filter(Sale.status != 9,
                func.date(Sale.sale_date) >= start_date,
                func.date(Sale.sale_date) <= end_date).scalar()

    number_of_expenses = db.session.query(func.count(Expense.id))\
        .filter(Expense.status != 9,
                func.date(Expense.expense_date) >= start_date,
                func.date(Expense.expense_date) <= end_date).scalar()

    return jsonify({
        "period": period,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "totalProducts": total_products,
        "totalSales": float(total_sales),
        "totalExpenses": float(total_expenses),
        "totalCustomers": total_customers,
        "totalSuppliers": total_suppliers,
        "totalPurchaseOrders": total_purchase_orders,
        "outstandingSales": float(outstanding_sales),
        "outstandingPO": float(outstanding_po),
        "salesLast7Days": sales_last_7_days,
        "expensesLast7Days": expenses_last_7_days,
        "bestPerformingProducts": best_products,
        "leastPerformingProducts": least_products,
        "sales_profit": round(total_profit, 2),
        "profitInRange": profit_in_range,
        "numberOfSales": number_of_sales,
        "numberOfExpenses": number_of_expenses
    })
