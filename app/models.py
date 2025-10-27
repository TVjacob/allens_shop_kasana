from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from sqlalchemy import Enum
# ------------------ Mixin for Status ------------------
class StatusMixin:
    status = db.Column(db.Integer, default=1, nullable=False)  # 1 = Active, 0 = Inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ Transaction Numbers ------------------
class TransactionNumber(db.Model, StatusMixin):
    id = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(10), nullable=False)  # e.g., INV, PO, PAY, EXP
    last_number = db.Column(db.Integer, default=0)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ Customer Table ------------------
class Customer(db.Model, StatusMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='Walk-in')
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(255))

    def __repr__(self):
        return f"<Customer {self.name}>"

# ------------------ Product & Inventory ------------------
class Category(db.Model, StatusMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

class Product(db.Model, StatusMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=False, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0)
    # created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ Suppliers & Purchase Orders ------------------
class Supplier(db.Model, StatusMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50))
    email = db.Column(db.String(100))

class PurchaseOrder(db.Model, StatusMixin):
    __tablename__ = 'purchase_order'

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    invoice_number = db.Column(db.String(50), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    memo = db.Column(db.String(255))
    received_at = db.Column(db.DateTime)
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'))

    # Financial fields
    total_amount = db.Column(db.Float, default=0)    # sum of all items
    total_paid = db.Column(db.Float, default=0)      # payments made
    total_balance = db.Column(db.Float, default=0)   # total_amount - total_paid
    status= db.Column(db.Integer, nullable=False,default=1)


    supplier = db.relationship('Supplier', backref='purchase_orders', lazy=True)
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PurchaseOrder {self.invoice_number}>"

    def update_totals(self):
        """Recalculate total_amount and total_balance based on items and payments."""
        self.total_amount = sum([item.total_price for item in self.items if item.status == 1])
        self.total_balance = self.total_amount - self.total_paid


class PurchaseOrderItem(db.Model, StatusMixin):
    __tablename__ = 'purchase_order_item'

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, default=0)
    total_price = db.Column(db.Float, default=0)  # quantity * unit_price
    status= db.Column(db.Integer, nullable=False,default=1)
    product = db.relationship('Product', backref='purchase_order_items', lazy=True)

    def __repr__(self):
        return f"<POItem ProductID={self.product_id} Qty={self.quantity}>"

    def calculate_total(self):
        """Update total_price based on quantity and unit_price."""
        self.total_price = self.quantity * self.unit_price

# class SupplierPayment(db.Model, StatusMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'))
#     amount = db.Column(db.Float, nullable=False)
#     payment_type = db.Column(db.String(20), default='Cash')  # Cash, Bank, Mobile Money
#     payment_date = db.Column(db.DateTime, default=datetime.utcnow)
#     reference = db.Column(db.String(100))
#     transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'))



class SupplierPayment(db.Model, StatusMixin):
    __tablename__ = 'supplier_payment'

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'))
    
    # Link to payment account
    payment_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(20), default='Cash')  # Cash, Bank, Mobile Money
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    reference = db.Column(db.String(100))
    # transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'))
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'), nullable=True)
    status = db.Column(db.Integer, default=1)



# ------------------ Sales & Invoices ------------------
# ------------------ Sales ------------------
class Sale(db.Model, StatusMixin):
    __tablename__ = 'sale'

    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(50), unique=True, nullable=False)

    # Customer
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False, default=1)  # Default Walk-in
    
    # Totals
    total_amount = db.Column(db.Float, default=0)     # Total for all items
    total_paid = db.Column(db.Float, default=0)       # Total amount paid
    balance = db.Column(db.Float, default=0)          # Remaining balance

    # Status
    payment_status = db.Column(db.String(20), default='Pending')  # Pending, Paid, Partial, Overpaid
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional: Transaction Tracking
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'), nullable=True)

    # Relationships
    customer = db.relationship('Customer', backref='sales', lazy=True)
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade="all, delete-orphan")
    status = db.Column(db.Integer, default=1)


    def update_totals(self):
        """Recalculate total_amount, balance, and update payment_status automatically."""
        self.total_amount = sum(item.total_price for item in self.items)
        self.balance = self.total_amount - self.total_paid

        if self.balance <= 0:
            self.payment_status = 'Paid'
        elif self.total_paid > 0 and self.balance > 0:
            self.payment_status = 'Partial'
        else:
            self.payment_status = 'Pending'


class SaleItem(db.Model, StatusMixin):
    __tablename__ = 'sale_item'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    product_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0)
    total_price = db.Column(db.Float, default=0)

    # Optional: Track which transaction added this item
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'), nullable=True)

    # Relationship
    product = db.relationship('Product', backref='sale_items', lazy=True)

    status = db.Column(db.Integer, default=1)


    def calculate_total(self):
        """Automatically calculate total_price."""
        self.total_price = self.quantity * self.unit_price


# class Invoice(db.Model, StatusMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'))
#     invoice_number = db.Column(db.String(50), unique=True, nullable=False)
#     transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
#     total_amount = db.Column(db.Float, default=0)
#     transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'))

# ------------------ Payments ------------------
class Payment(db.Model, StatusMixin):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(20))
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    reference = db.Column(db.String(100))
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'))
     
    # Link to payment account
    payment_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

# ------------------ Transaction Log ------------------
class InventoryTransaction(db.Model, StatusMixin):
    __tablename__ = 'inventory_transaction'

    id = db.Column(db.Integer, primary_key=True)
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'), nullable=False)  # link to GL

    # Source documents
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    # Transaction details
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, default=0)
    total_price = db.Column(db.Float, default=0)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'Purchase' or 'Sale'

    # Relationships
    product = db.relationship('Product', backref='inventory_transactions', lazy=True)
    purchase_order = db.relationship('PurchaseOrder', backref='inventory_transactions', lazy=True)
    sale = db.relationship('Sale', backref='inventory_transactions', lazy=True)
    transaction_number = db.relationship('TransactionNumber', backref='inventory_transactions', lazy=True)

    def __repr__(self):
        return f"<InventoryTransaction {self.transaction_type} - ProductID={self.product_id} Qty={self.quantity}>"


# ------------------ Permissions & Users ------------------
user_permissions = db.Table(
    'user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)

class Permission(db.Model, StatusMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

    def __repr__(self):
        return f"<Permission {self.name}>"

class User(db.Model, StatusMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    # password_hash = db.Column(db.String(128), nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)  # Increased size

    role = db.Column(db.String(20), default='Staff')

    # Permissions relationship
    permissions = db.relationship('Permission', secondary=user_permissions,
                                  backref=db.backref('users', lazy='dynamic'))

    # ---------------- Authentication Methods ----------------
    def set_password(self, password):
        """Hashes and sets the password for the user."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the hashed password."""
        return check_password_hash(self.password_hash, password)

    def has_permission(self, perm_name):
        """Check if user has a specific permission."""
        return any(p.name == perm_name for p in self.permissions)

    def add_permission(self, perm):
        """Assign a permission to the user."""
        if perm not in self.permissions:
            self.permissions.append(perm)

    def remove_permission(self, perm):
        """Remove a permission from the user."""
        if perm in self.permissions:
            self.permissions.remove(perm)

    def is_admin(self):
        """Optional: Check if user is admin based on role."""
        return self.role.lower() == 'admin'

    def __repr__(self):
        return f"<User {self.username}>"
    
# ------------------ Stock Adjustments ------------------
class StockAdjustment(db.Model, StatusMixin):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    adjustment_type = db.Column(db.String(20))
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200))
    adjusted_at = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'))

# ------------------ Expenses ------------------

# -------------------- Expense Header --------------------
class Expense(db.Model, StatusMixin):
    __tablename__ = 'expense'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)  # Overall memo/description
    expense_date = db.Column(db.DateTime, default=datetime.utcnow)  # Date of expense

    # The account from which payment was made (e.g., Cash, Bank)
    payment_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

    # Total paid for this expense transaction
    total_amount = db.Column(db.Float, default=0, nullable=False)

    # Reference or memo field
    reference = db.Column(db.String(100))

    # Link to a transaction number
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'))

    # Relationship to items
    items = db.relationship('ExpenseItem', backref='expense', lazy=True, cascade="all, delete-orphan")

    def update_total(self):
        """Recalculate total_amount based on expense items."""
        self.total_amount = sum(item.amount for item in self.items)

    def __repr__(self):
        return f"<Expense {self.id} - {self.description}>"


# -------------------- Expense Items --------------------
class ExpenseItem(db.Model, StatusMixin):
    __tablename__ = 'expense_item'

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)  # Link to Expense header

    # Link to Account to know which category this item belongs to (e.g., Utilities, Rent, etc.)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

    item_name = db.Column(db.String(100), nullable=False)  # Example: "Electricity Bill", "Printer Ink"
    description = db.Column(db.String(200))                # Optional details
    amount = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<ExpenseItem {self.item_name} - {self.amount}>"

# -------------------------------
# Enums for Account Types & Subtypes
# -------------------------------

class AccountTypeEnum(enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class AssetSubtypeEnum(enum.Enum):
    CASH = "Cash"
    ACCOUNTS_RECEIVABLE = "Accounts Receivable"
    INVENTORY = "Inventory"
    PREPAID_EXPENSES = "Prepaid Expenses"
    FIXED_ASSET = "Fixed Asset"
    BANK = "Bank"

class LiabilitySubtypeEnum(enum.Enum):
    ACCOUNTS_PAYABLE = "Accounts Payable"
    ACCRUED_LIABILITIES = "Accrued Liabilities"
    LONG_TERM_DEBT = "Long Term Debt"

class EquitySubtypeEnum(enum.Enum):
    OWNERS_EQUITY = "Owner's Equity"
    RETAINED_EARNINGS = "Retained Earnings"

class RevenueSubtypeEnum(enum.Enum):
    SALES = "Sales Revenue"
    SERVICE = "Service Revenue"

class ExpenseSubtypeEnum(enum.Enum):
    COGS = "Cost of Goods Sold"
    RENT = "Rent Expense"
    SALARIES = "Salaries Expense"
    UTILITIES = "Utilities Expense"


# -------------------------------
# Account Model
# -------------------------------
class Account(db.Model, StatusMixin):
    __tablename__ = 'account'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    
    account_type = db.Column(Enum(AccountTypeEnum), nullable=False)  # Enum type
    account_subtype = db.Column(db.String(50))  # Optional, can validate dynamically or with subtype enums
    parent_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    description = db.Column(db.String(200))

    # Relationships
    children = db.relationship(
        'Account',
        backref=db.backref('parent', remote_side=[id]),
        lazy=True
    )
    expenses_paid = db.relationship('Expense', backref='payment_account', lazy=True)
    expense_items = db.relationship('ExpenseItem', backref='account', lazy=True)

    def __repr__(self):
        return f"<Account {self.code} - {self.name}>"
    
# ------------------ General Ledger ------------------
class GeneralLedger(db.Model, StatusMixin):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'))
