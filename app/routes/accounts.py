import enum
from flask import Blueprint, request, jsonify
from app import db
from app.models import Account, AccountTypeEnum, AssetSubtypeEnum, LiabilitySubtypeEnum, EquitySubtypeEnum, RevenueSubtypeEnum, ExpenseSubtypeEnum
from datetime import datetime, timezone
from app.utils.auth import token_required, permission_required

accounts_bp = Blueprint('accounts', __name__, url_prefix='/accounts')

# -------------------------------
# Helper Functions
# -------------------------------

def enum_to_str(enum_val):
    return enum_val.value if isinstance(enum_val, enum.Enum) else enum_val

def generate_account_code(account_type, last_code=None):
    """
    Generate next unique account code automatically based on type prefix.
    Ensures code does not already exist in the database.
    """
    type_prefix = {
        "ASSET": "1",
        "LIABILITY": "2",
        "EQUITY": "3",
        "REVENUE": "4",
        "EXPENSE": "5"
    }.get(account_type.upper(), "9")

    # from app.models import Account  # make sure Account is imported

    # Start code generation
    if last_code:
        try:
            next_num = int(last_code)
        except ValueError:
            next_num = int(type_prefix + "000")
    else:
        next_num = int(type_prefix + "000")

    # Loop until a unique code is found
    while True:
        code_candidate = str(next_num)
        exists = Account.query.filter_by(code=code_candidate).first()
        if not exists:
            return code_candidate
        next_num += 10  # increment by 10 as before

# -------------------------------
# Routes with Permissions
# -------------------------------

@accounts_bp.route('/', methods=['POST'])
@token_required
@permission_required("create_journal_entry")  # Permission to add accounts
def add_account():
    data = request.json
    last_account = Account.query.filter_by(account_type=data['account_type']).order_by(Account.code.desc()).first()
    code = data.get('code') or generate_account_code(data['account_type'], last_account.code if last_account else None)

    account = Account(
        name=data['name'],
        code=code,
        account_type=data['account_type'],
        account_subtype=data.get('account_subtype'),
        parent_id=data.get('parent_id'),
        description=data.get('description'),
        status=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.session.add(account)
    db.session.commit()
    return jsonify({"message": "Account added", "account_id": account.id, "code": account.code}), 201

@accounts_bp.route('/', methods=['GET'])
@token_required
@permission_required("view_ledger")  # Permission to view accounts
def get_accounts():
    accounts = Account.query.filter(Account.status != 9).all()
    data = []
    for a in accounts:
        data.append({
            "id": a.id,
            "name": a.name,
            "code": a.code,
            "account_type": enum_to_str(a.account_type),
            "account_subtype": a.account_subtype,
            "description": a.description,
            "status": a.status,
            "parent_id":  a.parent_id,
            "parent_name": Account.query.filter(Account.id == a.parent_id).first().name if a.parent_id else "",
            "created_at": a.created_at,
            "updated_at": a.updated_at
        })
    return jsonify(data)

@accounts_bp.route('/<int:id>', methods=['GET'])
@token_required
@permission_required("view_ledger")
def get_account(id):
    a = Account.query.get_or_404(id)
    return jsonify({
        "id": a.id,
        "name": a.name,
        "code": a.code,
        "account_type": enum_to_str(a.account_type),
        "account_subtype": a.account_subtype,
        "description": a.description,
        "status": a.status,
        "parent_id": a.parent_id,
        "parent_name": Account.query.filter(Account.id == a.parent_id).first().name if a.parent_id else "",
        "created_at": a.created_at,
        "updated_at": a.updated_at
    })

@accounts_bp.route('/<int:id>', methods=['PUT'])
@token_required
@permission_required("edit_journal_entry")
def update_account(id):
    a = Account.query.get_or_404(id)
    data = request.json
    a.name = data.get('name', a.name)
    a.code = data.get('code', a.code)
    a.account_type = data.get('account_type', a.account_type)
    a.account_subtype = data.get('account_subtype', a.account_subtype)
    a.parent_id = data.get('parent_id', a.parent_id)
    a.description = data.get('description', a.description)
    a.updated_at = datetime.now(timezone.utc)
    a.status = data.get('status', a.status)
    db.session.commit()
    return jsonify({"message": "Account updated", "account_id": a.id})

@accounts_bp.route('/<int:id>', methods=['DELETE'])
@token_required
@permission_required("delete_journal_entry")
def delete_account(id):
    a = Account.query.get_or_404(id)
    a.status = 9  # Soft delete
    a.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"message": "Account soft deleted", "account_id": id})

@accounts_bp.route('/expense-items', methods=['POST'])
@token_required
@permission_required("create_journal_entry")
def create_expense_account():
    data = request.json
    name = data.get('name')
    subtype = data.get('account_subtype')
    if not name or not subtype:
        return jsonify({"error": "name and account_subtype are required"}), 400

    last_account = Account.query.filter_by(account_type="EXPENSE").order_by(Account.code.desc()).first()
    code = generate_account_code("EXPENSE", last_account.code if last_account else None)

    account = Account(
        name=name,
        code=code,
        account_type="EXPENSE",
        account_subtype=subtype,
        status=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.session.add(account)
    db.session.commit()
    return jsonify({"message": "Expense account created", "account_id": account.id, "code": account.code}), 201

@accounts_bp.route('/cash-bank', methods=['GET'])
@token_required
@permission_required("view_ledger")
def get_cash_and_bank():
    search = request.args.get('search', '')
    if search:
        accounts = Account.query.filter(
            Account.account_type == "ASSET",
            Account.account_subtype.in_([AssetSubtypeEnum.CASH.value, AssetSubtypeEnum.BANK.value]),
            Account.name.ilike(f"%{search}%")
        ).all()
    else:
        accounts = Account.query.filter(
            Account.account_type == "ASSET",
            Account.account_subtype.in_([AssetSubtypeEnum.CASH.value, AssetSubtypeEnum.BANK.value])
        ).all()
    data = [{"id": a.id, "name": a.name, "code": a.code, "account_subtype": a.account_subtype} for a in accounts]
    return jsonify(data)

@accounts_bp.route('/expense-account', methods=['GET'])
@token_required
@permission_required("view_ledger")
def get_expense_account():
    search = request.args.get('search', '')
    if search:
        accounts = Account.query.filter(
            Account.account_type == "EXPENSE",
            Account.name.ilike(f"%{search}%")
        ).all()
    else:
        accounts = Account.query.filter(Account.account_type == "EXPENSE").all()
    data = [{"id": a.id, "name": a.name, "code": a.code, "account_subtype": a.account_subtype} for a in accounts]
    return jsonify(data)






# import enum
# from flask import Blueprint, request, jsonify
# from app import db
# from app.models import Account,AccountTypeEnum,AssetSubtypeEnum,LiabilitySubtypeEnum,EquitySubtypeEnum,RevenueSubtypeEnum,ExpenseSubtypeEnum
# from datetime import datetime, timezone
# from app.utils.auth import token_required

# accounts_bp = Blueprint('accounts', __name__, url_prefix='/accounts')

# # -------------------------------
# # Enums for Account Types & Subtypes
# # -------------------------------
# # class AccountTypeEnum(enum.Enum):
# #     ASSET = "ASSET"
# #     LIABILITY = "LIABILITY"
# #     EQUITY = "EQUITY"
# #     REVENUE = "REVENUE"
# #     EXPENSE = "EXPENSE"

# # class AssetSubtypeEnum(enum.Enum):
# #     CASH = "Cash"
# #     ACCOUNTS_RECEIVABLE = "Accounts Receivable"
# #     INVENTORY = "Inventory"
# #     PREPAID_EXPENSES = "Prepaid Expenses"
# #     FIXED_ASSET = "Fixed Asset"

# # class LiabilitySubtypeEnum(enum.Enum):
# #     ACCOUNTS_PAYABLE = "Accounts Payable"
# #     ACCRUED_LIABILITIES = "Accrued Liabilities"
# #     LONG_TERM_DEBT = "Long Term Debt"

# # class EquitySubtypeEnum(enum.Enum):
# #     OWNERS_EQUITY = "Owner's Equity"
# #     RETAINED_EARNINGS = "Retained Earnings"

# # class RevenueSubtypeEnum(enum.Enum):
# #     SALES = "Sales Revenue"
# #     SERVICE = "Service Revenue"

# # class ExpenseSubtypeEnum(enum.Enum):
# #     COGS = "Cost of Goods Sold"
# #     RENT = "Rent Expense"
# #     SALARIES = "Salaries Expense"
# #     UTILITIES = "Utilities Expense"

# # # -------------------------------
# # Helper Functions
# # -------------------------------

# def enum_to_str(enum_val):
#     return enum_val.value if isinstance(enum_val, enum.Enum) else enum_val

# def generate_account_code(account_type, last_code=None):
#     """
#     Generate next account code automatically based on type prefix.
#     Example prefixes:
#         ASSET: 1xxx
#         LIABILITY: 2xxx
#         EQUITY: 3xxx
#         REVENUE: 4xxx
#         EXPENSE: 5xxx
#     """
#     type_prefix = {
#         "ASSET": "1",
#         "LIABILITY": "2",
#         "EQUITY": "3",
#         "REVENUE": "4",
#         "EXPENSE": "5"
#     }.get(account_type.upper(), "9")

#     if last_code:
#         try:
#             last_num = int(last_code)
#             next_code = str(last_num + 10)
#         except:
#             next_code = type_prefix + "000"
#     else:
#         next_code = type_prefix + "000"
#     return next_code

# # -------------------------------
# # Routes
# # -------------------------------

# @accounts_bp.route('/', methods=['POST'])
# @token_required
# def add_account():
#     data = request.json
#     # Auto-generate code if not provided
#     last_account = Account.query.filter_by(account_type=data['account_type']).order_by(Account.code.desc()).first()
#     code = data.get('code') or generate_account_code(data['account_type'], last_account.code if last_account else None)

#     account = Account(
#         name=data['name'],
#         code=code,
#         account_type=data['account_type'],
#         account_subtype=data.get('account_subtype'),
#         parent_id=data.get('parent_id'),
#         description=data.get('description'),
#         status=1,
#         created_at=datetime.now(timezone.utc),
#         updated_at=datetime.now(timezone.utc)
#     )
#     db.session.add(account)
#     db.session.commit()
#     return jsonify({
#         "message": "Account added",
#         "account_id": account.id,
#         "code": account.code
#     }), 201

# @accounts_bp.route('/', methods=['GET'])
# @token_required
# def get_accounts():
#     accounts = Account.query.filter(Account.status != 9).all()
#     data = []
#     for a in accounts:
#         data.append({
#             "id": a.id,
#             "name": a.name,
#             "code": a.code,
#             "account_type": enum_to_str(a.account_type),
#             "account_subtype": a.account_subtype,
#             "description": a.description,
#             "status": a.status,
#             "parent_id":  a.parent_id,
#             "parent_name": Account.query.filter(Account.id == a.parent_id).first().name if a.parent_id else "",
#             "created_at": a.created_at,
#             "updated_at": a.updated_at
#         })
#     return jsonify(data)

# @accounts_bp.route('/<int:id>', methods=['GET'])
# @token_required
# def get_account(id):
#     a = Account.query.get_or_404(id)
#     return jsonify({
#         "id": a.id,
#         "name": a.name,
#         "code": a.code,
#         "account_type": enum_to_str(a.account_type),
#         "account_subtype": a.account_subtype,
#         "description": a.description,
#         "status": a.status,
#         "parent_id": a.parent_id,
#         "parent_name": Account.query.filter(Account.id == a.parent_id).first().name if a.parent_id else "",
#         "created_at": a.created_at,
#         "updated_at": a.updated_at
#     })

# @accounts_bp.route('/<int:id>', methods=['PUT'])
# @token_required
# def update_account(id):
#     a = Account.query.get_or_404(id)
#     data = request.json
#     a.name = data.get('name', a.name)
#     a.code = data.get('code', a.code)
#     a.account_type = data.get('account_type', a.account_type)
#     a.account_subtype = data.get('account_subtype', a.account_subtype)
#     a.parent_id = data.get('parent_id', a.parent_id)
#     a.description = data.get('description', a.description)
#     a.updated_at = datetime.now(timezone.utc)
#     a.status = data.get('status', a.status)
#     db.session.commit()
#     return jsonify({"message": "Account updated", "account_id": a.id})

# @accounts_bp.route('/<int:id>', methods=['DELETE'])
# @token_required
# def delete_account(id):
#     a = Account.query.get_or_404(id)
#     a.status = 9  # Soft delete
#     a.updated_at = datetime.now(timezone.utc)
#     db.session.commit()
#     return jsonify({"message": "Account soft deleted", "account_id": id})

# # -------------------------------
# # Create expense account dynamically
# # -------------------------------
# @accounts_bp.route('/expense-items', methods=['POST'])
# @token_required
# def create_expense_account():
#     data = request.json
#     name = data.get('name')
#     subtype = data.get('account_subtype')
#     if not name or not subtype:
#         return jsonify({"error": "name and account_subtype are required"}), 400

#     last_account = Account.query.filter_by(account_type="EXPENSE").order_by(Account.code.desc()).first()
#     code = generate_account_code("EXPENSE", last_account.code if last_account else None)

#     account = Account(
#         name=name,
#         code=code,
#         account_type="EXPENSE",
#         account_subtype=subtype,
#         status=1,
#         created_at=datetime.now(timezone.utc),
#         updated_at=datetime.now(timezone.utc)
#     )
#     db.session.add(account)
#     db.session.commit()
#     return jsonify({"message": "Expense account created", "account_id": account.id, "code": account.code}), 201

# # -------------------------------
# # Get Cash and Bank accounts
# # -------------------------------
# @accounts_bp.route('/cash-bank', methods=['GET'])
# @token_required
# def get_cash_and_bank():
#     search = request.args.get('search', '')
#     if search:
#         accounts = Account.query.filter(
#             Account.account_type == "ASSET",
#             Account.account_subtype.in_([AssetSubtypeEnum.CASH.value, AssetSubtypeEnum.BANK.value]),
#             Account.name.ilike(f"%{search}%")
#         ).all()
#     else:
#         accounts = Account.query.filter(
#             Account.account_type == "ASSET",
#             Account.account_subtype.in_([AssetSubtypeEnum.CASH.value, AssetSubtypeEnum.BANK.value])
#         ).all()
#     data = [{
#         "id": a.id,
#         "name": a.name,
#         "code": a.code,
#         "account_subtype": a.account_subtype
#     } for a in accounts]
#     return jsonify(data)

# # -------------------------------
# # Get Expense  accounts
# # -------------------------------
# @accounts_bp.route('/expense-account', methods=['GET'])
# @token_required
# def get_expense_account():
#     search = request.args.get('search', '')
#     if search:
#         accounts = Account.query.filter(
#             Account.account_type == "EXPENSE",
#             Account.name.ilike(f"%{search}%")
#         ).all()
#     else:
#         accounts = Account.query.filter(
#             Account.account_type == "EXPENSE",
#         ).all()
#     data = [{
#         "id": a.id,
#         "name": a.name,
#         "code": a.code,
#         "account_subtype": a.account_subtype
#     } for a in accounts]
#     return jsonify(data)

# # -------------------------------
# # Chart of Accounts
# # -------------------------------
def build_chart(accounts):
    """ Recursively build chart of accounts hierarchy """
    def build_node(acc):
        return {
            "id": acc.id,
            "name": acc.name,
            "code": acc.code,
            "account_type": enum_to_str(acc.account_type),
            "account_subtype": acc.account_subtype,
            "children": [build_node(child) for child in acc.children if child.status != 9]
        }
    top_level = [a for a in accounts if not a.parent_id and a.status != 9]
    return [build_node(a) for a in top_level]

# @accounts_bp.route('/chart', methods=['GET'])
# @token_required
# def get_chart_of_accounts():
#     accounts = Account.query.all()
#     return jsonify(build_chart(accounts))


def build_chart_grouped(accounts):
    """
    Build Chart of Accounts grouped by type with totals and children.
    """
    # Group by account type
    grouped = {}
    for atype in AccountTypeEnum:
        grouped[atype.value] = []

    # Recursive function to build hierarchy
    def build_node(acc):
        children = [build_node(child) for child in acc.children if child.status != 9]
        return {
            "id": acc.id,
            "name": acc.name,
            "code": acc.code,
            "account_subtype": acc.account_subtype,
            "children": children,
            "child_count": len(children)
        }

    # Assign accounts to their group
    top_level_accounts = [a for a in accounts if not a.parent_id and a.status != 9]
    for acc in top_level_accounts:
        grouped[acc.account_type.value].append(build_node(acc))

    # Compute totals per group
    totals = {}
    for atype, acc_list in grouped.items():
        # For demo purposes, we'll use count of accounts as "total"
        def count_nodes(nodes):
            total = 0
            for n in nodes:
                total += 1
                if n['children']:
                    total += count_nodes(n['children'])
            return total
        totals[atype] = count_nodes(acc_list)

    return {"grouped_accounts": grouped, "totals": totals}


# @accounts_bp.route('/chart-report', methods=['GET'])
# @token_required
# def chart_of_accounts_report():
#     accounts = Account.query.all()
#     report = build_chart_grouped(accounts)
#     return jsonify(report)


@accounts_bp.route('/chart', methods=['GET'])
@token_required
@permission_required("view_ledger")
def get_chart_of_accounts():
    accounts = Account.query.all()
    return jsonify(build_chart(accounts))

@accounts_bp.route('/chart-report', methods=['GET'])
@token_required
@permission_required("view_ledger")
def chart_of_accounts_report():
    accounts = Account.query.all()
    report = build_chart_grouped(accounts)
    return jsonify(report)