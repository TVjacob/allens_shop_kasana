from app import create_app, db
from datetime import datetime,timezone
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, OperationalError, IntegrityError
from sqlalchemy import text

from app.models import AssetSubtypeEnum, EquitySubtypeEnum, ExpenseSubtypeEnum, InventoryTransaction, LiabilitySubtypeEnum, Product, PurchaseOrderItem, RevenueSubtypeEnum, Sale, SaleItem, TransactionNumber
from datetime import datetime, timezone

from app.routes.accounts import generate_account_code
from app.utils.gl_utils import generate_transaction_number_partone

app = create_app()


# Mapping of accounts with proper enum subtypes and parent_id
account_updates = [
    {"id": 1, "name": "Cash on Hand", "account_subtype": AssetSubtypeEnum.CASH, "parent_id": None, "description": "Cash on Hand"},
    {"id": 2, "name": "Petty Cash", "account_subtype": AssetSubtypeEnum.CASH, "parent_id": 1, "description": "Petty Cash"},
    {"id": 3, "name": "MTN Mobile Money", "account_subtype": AssetSubtypeEnum.CASH, "parent_id": 1, "description": "MTN Mobile Money"},
    {"id": 4, "name": "Airtel Money", "account_subtype": AssetSubtypeEnum.CASH, "parent_id": 1, "description": "Airtel Money"},
    {"id": 5, "name": "Other Mobile Wallets", "account_subtype": AssetSubtypeEnum.CASH, "parent_id": 1, "description": "Other Mobile Wallets"},
    {"id": 6, "name": "Stanbic Bank Account", "account_subtype": AssetSubtypeEnum.BANK, "parent_id": None, "description": "Stanbic Bank Account"},
    {"id": 7, "name": "Equity Bank Account", "account_subtype": AssetSubtypeEnum.BANK, "parent_id": None, "description": "Equity Bank Account"},
    {"id": 8, "name": "Centenary Bank Account", "account_subtype": AssetSubtypeEnum.BANK, "parent_id": None, "description": "Centenary Bank Account"},
    {"id": 9, "name": "Other Bank Accounts", "account_subtype": AssetSubtypeEnum.BANK, "parent_id": None, "description": "Other Bank Accounts"},
    {"id": 10, "name": "Accounts Receivable", "account_subtype": AssetSubtypeEnum.ACCOUNTS_RECEIVABLE, "parent_id": None, "description": "Accounts Receivable"},
    {"id": 11, "name": "Employee Advances", "account_subtype": AssetSubtypeEnum.PREPAID_EXPENSES, "parent_id": None, "description": "Employee Advances"},
    {"id": 12, "name": "Inventory", "account_subtype": AssetSubtypeEnum.INVENTORY, "parent_id": None, "description": "Inventory"},
    {"id": 13, "name": "Prepaid Expenses", "account_subtype": AssetSubtypeEnum.PREPAID_EXPENSES, "parent_id": None, "description": "Prepaid Expenses"},
    {"id": 14, "name": "Fixed Assets", "account_subtype": AssetSubtypeEnum.FIXED_ASSET, "parent_id": None, "description": "Fixed Assets"},
    {"id": 15, "name": "Accounts Payable", "account_subtype": LiabilitySubtypeEnum.ACCOUNTS_PAYABLE, "parent_id": None, "description": "Accounts Payable"},
    {"id": 16, "name": "Accrued Expenses", "account_subtype": LiabilitySubtypeEnum.ACCRUED_LIABILITIES, "parent_id": None, "description": "Accrued Expenses"},
    {"id": 17, "name": "Taxes Payable", "account_subtype": LiabilitySubtypeEnum.ACCRUED_LIABILITIES, "parent_id": None, "description": "Taxes Payable"},
    {"id": 18, "name": "Wages Payable", "account_subtype": LiabilitySubtypeEnum.ACCRUED_LIABILITIES, "parent_id": None, "description": "Wages Payable"},
    {"id": 19, "name": "Loan Payable", "account_subtype": LiabilitySubtypeEnum.LONG_TERM_DEBT, "parent_id": None, "description": "Loan Payable"},
    {"id": 20, "name": "Mobile Money Payable", "account_subtype": LiabilitySubtypeEnum.ACCOUNTS_PAYABLE, "parent_id": None, "description": "Mobile Money Payable"},
    {"id": 21, "name": "Credit Card Payable", "account_subtype": LiabilitySubtypeEnum.ACCOUNTS_PAYABLE, "parent_id": None, "description": "Credit Card Payable"},
    {"id": 22, "name": "Owner's Equity", "account_subtype": EquitySubtypeEnum.OWNERS_EQUITY, "parent_id": None, "description": "Owner's Equity"},
    {"id": 23, "name": "Retained Earnings", "account_subtype": EquitySubtypeEnum.RETAINED_EARNINGS, "parent_id": None, "description": "Retained Earnings"},
    {"id": 24, "name": "Drawings", "account_subtype": EquitySubtypeEnum.OWNERS_EQUITY, "parent_id": None, "description": "Drawings"},
    {"id": 25, "name": "Sales Revenue", "account_subtype": RevenueSubtypeEnum.SALES, "parent_id": None, "description": "Sales Revenue"},
    {"id": 26, "name": "Service Revenue", "account_subtype": RevenueSubtypeEnum.SERVICE, "parent_id": 25, "description": "Service Revenue"},
    {"id": 27, "name": "Mobile Money Income", "account_subtype": RevenueSubtypeEnum.SERVICE, "parent_id": 25, "description": "Mobile Money Income"},
    {"id": 28, "name": "Bank Transfer Income", "account_subtype": RevenueSubtypeEnum.SERVICE, "parent_id": 25, "description": "Bank Transfer Income"},
    {"id": 29, "name": "Other Income", "account_subtype": RevenueSubtypeEnum.SERVICE, "parent_id": 25, "description": "Other Income"},
    {"id": 30, "name": "Cost of Goods Sold", "account_subtype": ExpenseSubtypeEnum.COGS, "parent_id": None, "description": "Cost of Goods Sold"},
    {"id": 31, "name": "Rent Expense", "account_subtype": ExpenseSubtypeEnum.RENT, "parent_id": None, "description": "Rent Expense"},
    {"id": 32, "name": "Salaries & Wages Expense", "account_subtype": ExpenseSubtypeEnum.SALARIES, "parent_id": None, "description": "Salaries & Wages Expense"},
    {"id": 33, "name": "Overtime Expense", "account_subtype": ExpenseSubtypeEnum.SALARIES, "parent_id": 32, "description": "Overtime Expense"},
    {"id": 34, "name": "Employee Benefits Expense", "account_subtype": ExpenseSubtypeEnum.SALARIES, "parent_id": 32, "description": "Employee Benefits Expense"},
    {"id": 35, "name": "Utilities Expense", "account_subtype": ExpenseSubtypeEnum.UTILITIES, "parent_id": None, "description": "Utilities Expense"},
    {"id": 36, "name": "Office Supplies Expense", "account_subtype": ExpenseSubtypeEnum.OFFICE_SUPPLIES, "parent_id": None, "description": "Office Supplies Expense"},
    {"id": 37, "name": "Cleaning Supplies Expense", "account_subtype": ExpenseSubtypeEnum.OFFICE_SUPPLIES, "parent_id": 36, "description": "Cleaning Supplies Expense"},
    {"id": 38, "name": "Waste Management Expense", "account_subtype": ExpenseSubtypeEnum.OTHER_EXPENSES, "parent_id": None, "description": "Waste Management Expense"},
    {"id": 39, "name": "Repairs & Maintenance Expense", "account_subtype": ExpenseSubtypeEnum.OTHER_EXPENSES, "parent_id": None, "description": "Repairs & Maintenance Expense"},
    {"id": 40, "name": "IT Maintenance Expense", "account_subtype": ExpenseSubtypeEnum.OTHER_EXPENSES, "parent_id": None, "description": "IT Maintenance Expense"},
    {"id": 41, "name": "Depreciation Expense", "account_subtype": ExpenseSubtypeEnum.OTHER_EXPENSES, "parent_id": None, "description": "Depreciation Expense"},
    {"id": 42, "name": "Insurance Expense", "account_subtype": ExpenseSubtypeEnum.OTHER_EXPENSES, "parent_id": None, "description": "Insurance Expense"},
    {"id": 43, "name": "Bank Charges Expense", "account_subtype": ExpenseSubtypeEnum.BANK_FEES, "parent_id": None, "description": "Bank Charges Expense"},
    {"id": 44, "name": "Mobile Money Charges Expense", "account_subtype": ExpenseSubtypeEnum.BANK_FEES, "parent_id": None, "description": "Mobile Money Charges Expense"},
    {"id": 45, "name": "Credit Card Fees Expense", "account_subtype": ExpenseSubtypeEnum.BANK_FEES, "parent_id": None, "description": "Credit Card Fees Expense"},
    {"id": 46, "name": "Advertising Expense", "account_subtype": ExpenseSubtypeEnum.ADVERTISING, "parent_id": None, "description": "Advertising Expense"},
    {"id": 47, "name": "Promotional Expense", "account_subtype": ExpenseSubtypeEnum.ADVERTISING, "parent_id": 46, "description": "Promotional Expense"},
    {"id": 48, "name": "Travel Expense", "account_subtype": ExpenseSubtypeEnum.TRAVEL, "parent_id": None, "description": "Travel Expense"},
    {"id": 49, "name": "Training Expense", "account_subtype": ExpenseSubtypeEnum.TRAINING, "parent_id": None, "description": "Training Expense"},
    {"id": 50, "name": "Miscellaneous Expense", "account_subtype": ExpenseSubtypeEnum.OTHER_EXPENSES, "parent_id": None, "description": "Miscellaneous Expense"},
    {"id": 51, "name": "Interest Expense", "account_subtype": ExpenseSubtypeEnum.INTEREST, "parent_id": None, "description": "Interest Expense"},
    {"id": 52, "name": "Bank Loan Interest", "account_subtype": ExpenseSubtypeEnum.INTEREST, "parent_id": 51, "description": "Bank Loan Interest"},
    {"id": 53, "name": "Overdraft Interest", "account_subtype": ExpenseSubtypeEnum.INTEREST, "parent_id": 51, "description": "Overdraft Interest"},
    {"id": 54, "name": "Taxes Expense", "account_subtype": ExpenseSubtypeEnum.TAXES, "parent_id": None, "description": "Taxes Expense"},
    {"id": 55, "name": "VAT Payable", "account_subtype": ExpenseSubtypeEnum.TAXES, "parent_id": 54, "description": "VAT Payable"},
    {"id": 56, "name": "Income Tax Expense", "account_subtype": ExpenseSubtypeEnum.TAXES, "parent_id": 54, "description": "Income Tax Expense"},
]


permissions = [
    # --- User & Access Management ---
    ("view_users", "View list of users"),
    ("create_user", "Add new users"),
    ("edit_user", "Edit user details"),
    ("delete_user", "Remove a user"),
    ("view_roles", "View user roles"),
    ("manage_roles", "Create or edit roles"),
    ("view_permissions", "View permission list"),
    ("assign_permissions", "Assign or remove user permissions"),

    # --- Sales / Invoicing ---
    ("view_invoices", "View all sales invoices"),
    ("create_invoice", "Create a new invoice"),
    ("edit_invoice", "Edit existing invoices"),
    ("delete_invoice", "Delete an invoice"),
    ("approve_invoice", "Approve or finalize invoices"),
    ("export_invoices", "Export invoice data to Excel/PDF"),

    # --- Purchases / Suppliers ---
    ("view_purchases", "View purchase orders"),
    ("create_purchase", "Create a new purchase order"),
    ("edit_purchase", "Edit purchase records"),
    ("delete_purchase", "Delete a purchase order"),
    ("approve_purchase", "Approve supplier purchase requests"),
    ("export_purchases", "Export purchase reports"),

    # --- Inventory / Stock ---
    ("view_inventory", "View current inventory levels"),
    ("add_inventory_item", "Add new products/items"),
    ("edit_inventory_item", "Edit item details"),
    ("delete_inventory_item", "Remove items from stock"),
    ("adjust_stock", "Perform stock adjustments"),
    ("export_inventory", "Export inventory data"),

    # --- Accounting / Ledger ---
    ("view_ledger", "View general ledger entries"),
    ("create_journal_entry", "Add journal entries"),
    ("edit_journal_entry", "Edit existing entries"),
    ("delete_journal_entry", "Remove journal entries"),
    ("approve_journal_entry", "Approve accounting entries"),

    # --- Financial Reports ---
    ("view_balance_sheet", "View balance sheet report"),
    ("view_income_statement", "View income statement (P&L)"),
    ("view_cash_flow", "View cash flow statement"),
    ("view_trial_balance", "View trial balance"),
    ("view_debtors_aging", "View debtors aging report"),
    ("view_creditors_aging", "View creditors aging report"),
    ("export_reports", "Export reports to Excel/PDF"),

    # --- Customers / Debtors ---
    ("view_customers", "View customer list"),
    ("create_customer", "Add a new customer"),
    ("edit_customer", "Edit customer details"),
    ("delete_customer", "Remove customer"),
    ("view_customer_invoices", "View customer invoices"),
    ("send_customer_statement", "Send statements to customers"),

    # --- Suppliers / Creditors ---
    ("view_suppliers", "View supplier list"),
    ("create_supplier", "Add a new supplier"),
    ("edit_supplier", "Edit supplier details"),
    ("delete_supplier", "Remove supplier"),
    ("view_supplier_invoices", "View supplier invoices"),
    ("send_supplier_statement", "Send statements to suppliers"),

    # --- Settings / Configuration ---
    ("view_settings", "View system settings"),
    ("update_settings", "Modify system configuration"),
    ("manage_account_types", "Manage chart of accounts and account types"),
    ("backup_database", "Perform database backup"),
    ("restore_database", "Restore data from backup"),

    # --- Payroll (Optional) ---
    ("view_payroll", "View payroll records"),
    ("create_payroll", "Create new payroll run"),
    ("edit_payroll", "Edit payroll details"),
    ("delete_payroll", "Delete payroll record"),
    ("approve_payroll", "Approve payroll run"),
    # --- Miscellaneous ---
    ("view_reports", " View reports screen"),
    ("view_accounts", "View chart of accounts"),
    ("view_stock", "View stock levels"),
    ("view_sales","view sales dashboard"),
    ("view_expense","View all Expenses"),



]


def seed_permissions():
    """Insert permissions if they don’t already exist and assign all to admin."""
    with app.app_context():
        added = 0

        # 1️⃣ Get or create admin user
        admin_user = User.query.filter_by(username='admin').first()

        # 2️⃣ Seed permissions
        all_permissions = []
        for name, desc in permissions:
            existing = db.session.execute(
                db.select(Permission).filter_by(name=name)
            ).scalar_one_or_none()
            if not existing:
                perm = Permission(
                    name=name,
                    description=desc,
                    status=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(perm)
                all_permissions.append(perm)
                added += 1
            else:
                all_permissions.append(existing)

        db.session.commit()
        print(f"✅ {added} new permissions added successfully.")

        # 3️⃣ Assign all permissions to admin if admin exists
        if admin_user:
            for perm in all_permissions:
                admin_user.add_permission(perm)
            db.session.commit()
            print("✅ All permissions assigned to admin user.")




# def update_all_accounts():
#     try:
#         for acc in account_updates:

#             account = Account.query.filter_by(id=acc["id"]).first()
#             if account:
#                 # Convert enum to string
#                 subtype = acc.get("account_subtype")
#                 if subtype:
#                     account.account_subtype = subtype.value  # <-- key change
#                 account.parent_id = acc.get("parent_id")
#                 account.updated_at = datetime.now(timezone.utc)  # timezone-aware
#         db.session.commit()
#         print("✅ All 50 accounts updated successfully with ENUM subtypes and parent_id references.")
#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ Failed to update accounts: {e}")


# def update_all_accounts():
#     try:
#         for acc in account_updates:
#             # Check if account exists, create if not
#             existing_account = Account.query.filter_by(id=acc["id"]).first()
#             if not existing_account:
#                 # Create a new account
#                 existing_account = Account(
#                     id=acc.get("id"),
#                     name=acc.get("name", ""),
#                     code=acc.get("code", ""),
#                     account_type=acc.get("account_subtype").value,
#                     account_subtype=acc.get("account_subtype"),
#                     parent_id=None if not acc.get("parent_id") else acc.get("parent_id"),
#                     description=acc.get("description", "")
#                 )
#             # Update the account
#             existing_account.account_subtype = acc.get("account_subtype")
#             existing_account.parent_id = acc.get("parent_id")
#             existing_account.description = acc.get("description")
#             if acc:
#                 existing_account.updated_at = datetime.now(timezone.utc)
            
#             db.session.add(existing_account)
#         db.session.commit()
#         print(f"✅ All 50 accounts updated successfully with ENUM subtypes and parent_id references.")
#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ Failed to update accounts: {e}")


def update_all_accounts():
    """
    Update existing accounts or create missing ones based on account_updates mapping.
    Searches first by ID, then by name. Updates ID if name matches.
    Generates new account codes if account does not exist.
    """
    try:
        for acc in account_updates:
            account_id = acc.get("id")
            account_name = acc.get("name")
            subtype_enum = acc.get("account_subtype")
            parent_id = acc.get("parent_id")
            description = acc.get("description", "")

            # Determine account_type from the Enum class name
            account_type = subtype_enum.__class__.__name__.replace("SubtypeEnum", "").upper()

            # --- 1️⃣ Search by ID ---
            account = Account.query.filter_by(id=account_id).first()

            # --- 2️⃣ If not found, search by name ---
            if not account:
                account = Account.query.filter_by(name=account_name).first()
                if account:
                    # Update ID to match mapping
                    account.id = account_id

            # --- 3️⃣ Update or Create ---
            if account:
                # Update existing account
                account.name = account_name
                account.account_subtype = subtype_enum.value
                account.parent_id = parent_id
                account.description = description
                account.updated_at = datetime.now(timezone.utc)
            else:
                # Create new account
                last_account = (
                    Account.query.filter(Account.account_type == account_type)
                    .order_by(Account.code.desc())
                    .first()
                )
                last_code = last_account.code if last_account else None
                new_code = generate_account_code(account_type, last_code)

                new_acc = Account(
                    id=account_id,
                    name=account_name,
                    code=new_code,
                    account_type=account_type,
                    account_subtype=subtype_enum.value,
                    parent_id=parent_id,
                    description=description,
                    status=1,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.session.add(new_acc)

        db.session.commit()
        print("✅ All accounts updated or created successfully.")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to update or create accounts: {e}")



def normalize_account_type_enum_uppercase():
    print("🔄 Converting account_type to uppercase enum...")

    with app.app_context():
        try:
            db.session.execute(text("""
                ALTER TYPE accounttypeenum RENAME TO accounttypeenum_old;
            """))
            db.session.execute(text("""
                CREATE TYPE accounttypeenum AS ENUM ('ASSET','LIABILITY','EQUITY','REVENUE','EXPENSE');
            """))
            db.session.execute(text("""
                ALTER TABLE account
                ALTER COLUMN account_type TYPE accounttypeenum
                USING UPPER(account_type::text)::accounttypeenum;
            """))
            db.session.execute(text("""
                DROP TYPE accounttypeenum_old;
            """))
            db.session.commit()
            print("✅ account_type is now uppercase and enum-safe.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to normalize account_type: {e}")



def create_default_admin():
    """Create a default admin user if not already present."""
    existing_user = User.query.filter_by(username='admin').first()
    if existing_user:
        print("ℹ️ Admin user already exists.")
        return

    try:
        admin = User(
            username='admin',
            role='Admin',
            password_hash=generate_password_hash('123456')
        )

        # Assign all permissions
        for perm in Permission.query.all():
            admin.add_permission(perm)

        db.session.add(admin)
        db.session.commit()
        print("✅ Default admin user created (Username: admin | Password: 123456)")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"❌ Failed to create admin user: {e}")


def fix_missing_purchase_order_transactions():
    """Fix purchase orders missing transaction_no."""
    missing = PurchaseOrder.query.filter_by(transaction_no=None).all()
    if not missing:
        print("ℹ️ No purchase orders with missing transaction numbers.")
        return

    for po in missing:
        po.update_totals()
        total = po.total_amount

        entries = [
            {"account_id": 1200, "transaction_type": "Debit", "amount": total},
            {"account_id": 2100, "transaction_type": "Credit", "amount": total},
        ]

        txn_id, _ = generate_transaction_number("CREDIT-PAY", transaction_date=po.purchase_date)
        po.transaction_no = txn_id

        post_to_ledger(
            entries,
            transaction_no_id=txn_id,
            description=f"Credit for PO #{po.id}",
            transaction_date=po.purchase_date
        )

        db.session.add(po)

    try:
        db.session.commit()
        print(f"✅ Fixed {len(missing)} purchase orders.")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"❌ Failed to update purchase orders: {e}")


# def seed_chart_of_accounts():
#     """Seed and assign chart of accounts, subtypes, and parents in one pass."""
#     predefined_accounts = [
#         # ASSETS
#         {"code": "1000", "name": "Cash on Hand", "account_type": "ASSET", "description": "Physical cash kept at the premises"},
#         {"code": "1010", "name": "Petty Cash", "account_type": "ASSET", "description": "Small cash for expenses"},
#         {"code": "1020", "name": "MTN Mobile Money", "account_type": "ASSET", "description": "MTN mobile money balance"},
#         {"code": "1030", "name": "Airtel Money", "account_type": "ASSET", "description": "Airtel mobile money balance"},
#         {"code": "1040", "name": "Other Mobile Wallets", "account_type": "ASSET", "description": "Other wallet balances"},
#         {"code": "1050", "name": "Stanbic Bank Account", "account_type": "ASSET", "description": "Stanbic bank account balance"},
#         {"code": "1060", "name": "Equity Bank Account", "account_type": "ASSET", "description": "Equity bank account balance"},
#         {"code": "1070", "name": "Centenary Bank Account", "account_type": "ASSET", "description": "Centenary bank account balance"},
#         {"code": "1080", "name": "Other Bank Accounts", "account_type": "ASSET", "description": "Secondary bank accounts"},
#         {"code": "1100", "name": "Accounts Receivable", "account_type": "ASSET", "description": "Money owed by customers"},
#         {"code": "1200", "name": "Inventory", "account_type": "ASSET", "description": "Goods available for sale"},
#         {"code": "1400", "name": "Fixed Assets", "account_type": "ASSET", "description": "Property, plant, and equipment"},
#         # LIABILITIES
#         {"code": "2000", "name": "Accounts Payable", "account_type": "LIABILITY", "description": "Money owed to suppliers"},
#         {"code": "2100", "name": "Accrued Expenses", "account_type": "LIABILITY", "description": "Expenses incurred but unpaid"},
#         # EQUITY
#         {"code": "3000", "name": "Owner's Equity", "account_type": "EQUITY", "description": "Owner capital"},
#         # REVENUE
#         {"code": "4000", "name": "Sales Revenue", "account_type": "REVENUE", "description": "Sales income"},
#         # EXPENSE
#         {"code": "5000", "name": "Cost of Goods Sold", "account_type": "EXPENSE", "description": "Direct cost of sales"},
#     ]

#     subtype_map = {
#         "ASSET": {"1000": "Cash", "1010": "Cash", "1050": "Bank"},
#         "LIABILITY": {"2000": "Current Liability", "2100": "Accrued"},
#         "EQUITY": {"3000": "Owner Equity"},
#         "REVENUE": {"4000": "Sales"},
#         "EXPENSE": {"5000": "COGS"},
#     }

#     parent_map = {"1000": None, "2000": None, "3000": None, "4000": None, "5000": None}

#     existing = {a.code: a for a in Account.query.all()}
#     added = []

#     for acc in predefined_accounts:
#         if acc["code"] in existing:
#             continue

#         new_acc = Account(
#             name=acc["name"],
#             code=acc["code"],
#             account_type=acc["account_type"],
#             description=acc["description"],
#             status=1,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow(),
#         )

#         subtype = subtype_map.get(acc["account_type"], {}).get(acc["code"])
#         if subtype:
#             new_acc.account_subtype = subtype

#         if acc["code"] not in parent_map:
#             parent_code = str(int(acc["code"]) // 1000 * 1000)
#             parent = existing.get(parent_code)
#             if parent:
#                 new_acc.parent_id = parent.id

#         db.session.add(new_acc)
#         existing[acc["code"]] = new_acc
#         added.append(acc["name"])

#     try:
#         db.session.commit()
#         print(f"✅ Seeded {len(added)} new accounts.")
#     except SQLAlchemyError as e:
#         db.session.rollback()
#         print(f"❌ Failed to seed accounts: {e}")


# def update_inventory_from_purchases():
#     """Add product quantities from received purchase orders."""
#     try:
#         purchase_items = PurchaseOrderItem.query.filter_by(status=1).all()
#         count = 0

#         for item in purchase_items:
#             product = Product.query.get(item.product_id)
#             if not product:
#                 continue

#             # Increase stock
#             product.quantity = (product.quantity or 0) + item.quantity
#             count += 1

#             # Log inventory transaction
#             # transaction_number = TransactionNumber(prefix="PO", last_number=item.purchase_order_id)
#             # db.session.add(transaction_number)
#             # db.session.flush()
#             # transaction_number = PurchaseOrder.query.get(item.purchase_order_id).first().transaction_no
#             purchase_order = PurchaseOrder.query.get(item.purchase_order_id)
#             transaction_number = purchase_order.transaction_no if purchase_order else None



#             transaction = InventoryTransaction(
#                 transaction_no=transaction_number,
#                 purchase_order_id=item.purchase_order_id,
#                 product_id=item.product_id,
#                 quantity=item.quantity,
#                 unit_price=item.unit_price,
#                 total_price=item.total_price,
#                 transaction_type="Purchase",
#                 created_at=datetime.utcnow()
#             )
#             db.session.add(transaction)

#         db.session.commit()
#         print(f"✅ Updated {count} product quantities from purchase orders.")

#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ Failed to update purchase orders: {e}")


# def update_inventory_from_sales():
#     """Subtract sold product quantities from stock."""
#     try:
#         sale_items = SaleItem.query.filter_by(status=1).all()
#         count = 0

#         for item in sale_items:
#             product = Product.query.get(item.product_id)
#             if not product:
#                 continue

#             # Decrease stock
#             product.quantity = max((product.quantity or 0) - item.quantity, 0)
#             count += 1

#             # Log inventory transaction
#             purchase_order = PurchaseOrder.query.get(item.purchase_order_id)
#             transaction_number = purchase_order.transaction_no if purchase_order else None

#             transaction = InventoryTransaction(
#                 transaction_no=transaction_number,
#                 sale_id=item.sale_id,
#                 product_id=item.product_id,
#                 quantity=item.quantity,
#                 unit_price=item.unit_price,
#                 total_price=item.total_price,
#                 transaction_type="Sale",
#                 created_at=datetime.utcnow()
#             )
#             db.session.add(transaction)

#         db.session.commit()
#         print(f"✅ Updated {count} product quantities from sales.")

#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ Failed to update sales: {e}")


# from sqlalchemy import text

# def rebuild_product_quantities():
#     """
#     Recalculate and rebuild product quantities:
#     SUM(all purchase quantities where status != 9)
#     MINUS SUM(all sale quantities where status != 9)
#     and update product.quantity in one pass.
#     """
#     try:
#         print("🔄 Rebuilding product quantities...")

#         sql = text("""
#         WITH purchase_totals AS (
#             SELECT product_id, COALESCE(SUM(quantity), 0) AS total_purchased
#             FROM purchase_order_item
#             WHERE status != 9
#             GROUP BY product_id
#         ),
#         sale_totals AS (
#             SELECT product_id, COALESCE(SUM(quantity), 0) AS total_sold
#             FROM sale_item
#             WHERE status != 9
#             GROUP BY product_id
#         )
#         UPDATE product p
#         SET quantity = 
#             COALESCE(pur.total_purchased, 0) - COALESCE(sal.total_sold, 0)
#         FROM purchase_totals pur
#         FULL JOIN sale_totals sal ON pur.product_id = sal.product_id
#         WHERE p.id = COALESCE(pur.product_id, sal.product_id);
#         """)

#         db.session.execute(sql)
#         db.session.commit()
#         print("✅ Product quantities successfully rebuilt based on purchases and sales.")

#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ Failed to rebuild product quantities: {e}")


# def sync_missing_inventory_transactions():
#     """
#     Finds purchase and sale items that are not yet in InventoryTransaction
#     and inserts them with correct transaction numbers.
#     """
#     try:
#         print("🔍 Scanning for missing inventory transactions...")

#         # --- 1️⃣ Missing Purchases ---
#         purchase_query = text("""
#             SELECT poi.id, poi.purchase_order_id, poi.product_id, poi.quantity, poi.unit_price, poi.total_price
#             FROM purchase_order_item poi
#             LEFT JOIN inventory_transaction it 
#                 ON it.purchase_order_id = poi.purchase_order_id AND it.product_id = poi.product_id
#                 AND it.transaction_type = 'Purchase'
#             WHERE it.id IS NULL AND poi.status != 9;
#         """)
#         purchase_items = db.session.execute(purchase_query).fetchall()

#         for row in purchase_items:
#             purchase_order = PurchaseOrder.query.get(row.purchase_order_id)
#             transaction_no,tstr = purchase_order.transaction_no if purchase_order else generate_transaction_number_partone(prefix="PURCHASE", transaction_date=row.purchase_date)
#             # if not transaction_no:
#             #     transaction_no = generate_transaction_number_partone("PURCHASE")

#             db.session.add(InventoryTransaction(
#                 transaction_no=transaction_no,
#                 purchase_order_id=row.purchase_order_id,
#                 product_id=row.product_id,
#                 quantity=row.quantity,
#                 unit_price=row.unit_price,
#                 total_price=row.total_price,
#                 transaction_type="Purchase",
#                 created_at=row.purchase_date
#             ))

#         # --- 2️⃣ Missing Sales ---
#         sale_query = text("""
#             SELECT si.id, si.sale_id, si.product_id, si.quantity, si.unit_price, si.total_price
#             FROM sale_item si
#             LEFT JOIN inventory_transaction it 
#                 ON it.sale_id = si.sale_id AND it.product_id = si.product_id
#                 AND it.transaction_type = 'Sale'
#             WHERE it.id IS NULL AND si.status != 9;
#         """)
#         sale_items = db.session.execute(sale_query).fetchall()

#         for row in sale_items:
#             sale = Sale.query.get(row.sale_id)
#             transaction_no, txn_str = sale.transaction_no if sale else generate_transaction_number_partone(prefix="SALE",transaction_date=row.sale_date)
#             # ✅ Auto-generate if missing
#             # if not transaction_no:
#             #     transaction_no = generate_transaction_number_partone("SALE")

#             db.session.add(InventoryTransaction(
#                 transaction_no=transaction_no,
#                 sale_id=row.sale_id,
#                 product_id=row.product_id,
#                 quantity=row.quantity,
#                 unit_price=row.unit_price,
#                 total_price=row.total_price,
#                 transaction_type="Sale",
#                 created_at=row.sale_date
#             ))

#         db.session.commit()
#         print(f"✅ Synced {len(purchase_items)} purchases and {len(sale_items)} sales to InventoryTransaction.")

#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ Failed to sync missing inventory transactions: {e}")


# def repair_inventory():
#     """Rebuild quantities and sync missing transactions."""
#     print("🧰 Running inventory repair...")
#     rebuild_product_quantities()
#     sync_missing_inventory_transactions()
#     print("✅ Inventory repair completed.")


def seed_product_units():
    """
    Seed the product_unit table:
    - For each product that has no product_unit records,
      create one called 'Bottle'
    - retail_price = Product.price
    - wholesale_price = Product.whole_price
    - is_returnable = False
    - conversion_quantity = 1
    - unit_name = 'Bottle'
    - unit_code = Product.sku (or track_no equivalent)
    """
    from app.models import Product, ProductUnit

    with app.app_context():
        try:
            products = Product.query.filter(Product.status==1).all()
            count_added = 0

            for product in products:
                # Check if this product already has any ProductUnit
                existing_unit = ProductUnit.query.filter_by(product_id=product.id).first()
                if existing_unit:
                    continue  # Skip if already seeded

                new_unit = ProductUnit(
                    product_id=product.id,
                    unit_name="Bottle",
                    conversion_quantity=1,
                    retail_price=product.price or 0,
                    wholesale_price=product.whole_price or 0,
                    is_returnable=False,
                    unit_code=product.sku,  # or track_no if that’s your code field
                    status=1,
                    cost_price= 0,
                )

                db.session.add(new_unit)
                count_added += 1

            db.session.commit()
            print(f"✅ Seeded {count_added} new product units (bottles).")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to seed product units: {e}")


if __name__ == "__main__":
    with app.app_context():
        from app.models import Account, PurchaseOrder, User, Permission
        from app.utils.gl_utils import generate_transaction_number, post_to_ledger
        # repair_inventory()
        seed_product_units()
        update_all_accounts()
        normalize_account_type_enum_uppercase()
        seed_permissions()
        # seed_chart_of_accounts()
        create_default_admin()
        fix_missing_purchase_order_transactions()

    app.run(debug=True, host='0.0.0.0', port=8990)

