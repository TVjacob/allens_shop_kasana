from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from sqlalchemy import Enum

# from datetime import datetime
from sqlalchemy import CheckConstraint
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
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
        }

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
    whole_price = db.Column(db.Float, default=0)
    category = db.relationship('Category', backref='products', lazy=True)

    # created_at = db.Column(db.DateTime, default=datetime.utcnow)




# class ProductUnit(db.Model, StatusMixin):
#     __tablename__ = 'product_unit'

#     id = db.Column(db.Integer, primary_key=True)
#     product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

#     # Name of the unit (Bottle, Dozen, Crate, etc.)
#     unit_name = db.Column(db.String(50), nullable=False)

#     # How many base units this represents (e.g. 1 crate = 12 bottles)
#     conversion_quantity = db.Column(db.Float, default=1.0, nullable=False)

#     # Prices specific to this unit
#     retail_price = db.Column(db.Float, default=0.0)
#     wholesale_price = db.Column(db.Float, default=0.0)

#     # Whether the unit is refundable (e.g. bottles that can be returned)
#     is_returnable = db.Column(db.Boolean, default=False)

#     # Optional field for barcode or code unique per unit
#     unit_code = db.Column(db.String(50), unique=False)

#     # Relationship
#     product = db.relationship('Product', backref=db.backref('units', lazy=True, cascade="all, delete-orphan"))

#     def __repr__(self):
#         return f"<ProductUnit {self.unit_name} of {self.product.name}>"

#     def get_total_price(self, quantity):
#         """Calculate total retail value for given quantity."""
#         return self.retail_price * quantity




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
    unit_id = db.Column(db.Integer, db.ForeignKey('product_unit.id'), nullable=True)

        # <-- Add this relationship
    unit = db.relationship('ProductUnit', backref='purchase_order_items', lazy=True)

    def __repr__(self):
        return f"<POItem ProductID={self.product_id} Qty={self.quantity}>"

    def calculate_total(self):
        """Update total_price based on quantity and unit_price."""
        self.total_price = round(self.quantity * self.unit_price)

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
    unit_id = db.Column(db.Integer, db.ForeignKey('product_unit.id'), nullable=True)


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
    COGS = "Cost of Goods Sold Expense"
    RENT = "Rent Expense"
    SALARIES = "Salaries Expense"
    UTILITIES = "Utilities Expense"
    OFFICE_SUPPLIES ="Office Supplies Expense"
    OTHER_EXPENSES="Other Expenses"
    BANK_FEES ="Banks fees Expense"
    ADVERTISING="Advertising Expense"
    TRAINING ="Training Expense"
    INTEREST ="Interest Expense"
    TRAVEL ="Travel Expense"
    TAXES= "Taxes Expense"


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


class BottleTransaction(db.Model, StatusMixin):
    __tablename__ = 'bottle_transaction'

    id = db.Column(db.Integer, primary_key=True)

    # Link to the crate/container and product unit
    container_id = db.Column(db.Integer, db.ForeignKey('returnable_container.id'), nullable=True)
    product_unit_id = db.Column(db.Integer, db.ForeignKey('product_unit.id'), nullable=False)

    # Link to sale or purchase
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)

    # Transaction info
    transaction_type = db.Column(db.String(20), nullable=False)  # 'Issued', 'Returned', 'Damaged', 'Received', 'Sold'
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Number of bottles
    unit_value = db.Column(db.Float, default=0.0)                # Cost per bottle
    total_value = db.Column(db.Float, default=0.0)               # unit_value * quantity

    # Store number of bottles sold
    bottles_sold = db.Column(db.Integer, default=0)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    container = db.relationship('ReturnableContainer', backref='bottle_transactions')
    product_unit = db.relationship('ProductUnit')
    sale = db.relationship('Sale', backref='bottle_transactions')
    purchase_order = db.relationship('PurchaseOrder', backref='bottle_transactions')
    customer = db.relationship('Customer', backref='bottle_transactions')

    def __repr__(self):
        return f"<BottleTransaction {self.transaction_type} {self.quantity} bottles from container {self.container_id}>"

    def calculate_total_value(self):
        self.total_value = self.quantity * self.unit_value
        return self.total_value


class ReturnableContainer(db.Model, StatusMixin):
    __tablename__ = 'returnable_container'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Beer Crate"
    description = db.Column(db.String(200))
    unit_value = db.Column(db.Float, default=0.0)    # Cost per container

    # Track stock
    total_issued = db.Column(db.Integer, default=0)     # Issued to customers
    total_returned = db.Column(db.Integer, default=0)   # Returned by customers
    total_damaged = db.Column(db.Integer, default=0)    # Damaged containers
    total_in_stock = db.Column(db.Integer, default=0)   # Current available stock

    # Track total sold
    total_sold = db.Column(db.Integer, default=0)       # Total crates/bottles sold

    # Link to ProductUnit (foreign key is here)
    product_unit_id = db.Column(db.Integer, db.ForeignKey('product_unit.id'), nullable=False)
    product_unit = db.relationship('ProductUnit', back_populates='containers')

    # Transactions
    transactions = db.relationship('ContainerTransaction', backref='container', lazy=True)

    __table_args__ = (
        CheckConstraint('total_in_stock >= 0', name='check_total_in_stock_non_negative'),
    )

    def __repr__(self):
        return f"<ReturnableContainer {self.name} for {self.product_unit.unit_name}>"

    @property
    def available_stock(self):
        """
        Returns the actual usable stock:
        total_in_stock = issued - returned - damaged
        """
        return self.total_issued - self.total_returned - self.total_damaged

    def process_transaction(self, transaction_type: str, quantity: int, sold: bool = False):
        """
        Update stock based on transaction type.
        transaction_type: 'Issued', 'Returned', 'Received', 'Damaged', 'Purchased'
        sold: True if this transaction is an actual sale
        """
        if transaction_type == 'Issued':
            self.total_issued += quantity
        elif transaction_type == 'Returned':
            self.total_returned += quantity
        elif transaction_type == 'Received':
            self.total_in_stock += quantity
        elif transaction_type == 'Damaged':
            self.total_damaged += quantity
        elif transaction_type == 'Purchased':
            self.total_in_stock += quantity
        elif transaction_type == "Sold":
            self.total_sold +=quantity
        elif transaction_type == 'Removed':
            self.total_sold -=quantity
            # self.total_returned +=quantity
        else:
            raise ValueError(f"Invalid transaction type: {transaction_type}")

        # if sold:
        #     self.total_sold += quantity

        # Ensure stock never goes negative
        if self.total_in_stock < 0:
            raise ValueError("Total in-stock cannot be negative after transaction")


class ContainerTransaction(db.Model, StatusMixin):
    __tablename__ = 'container_transaction'

    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, db.ForeignKey('returnable_container.id'), nullable=False)

    # Link to sale or purchase if applicable
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)

    transaction_type = db.Column(
        db.String(20),
        nullable=False
    )  # 'Issued', 'Returned', 'Received', 'Damaged','Purchased',"Sold","Removed"

    quantity = db.Column(db.Integer, nullable=False)
    unit_value = db.Column(db.Float, default=0.0)    # Cost per container
    total_value = db.Column(db.Float, default=0.0)   # unit_value * quantity

    # Track sold
    sold_quantity = db.Column(db.Integer, default=0)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sale = db.relationship('Sale', backref='container_transactions')
    purchase_order = db.relationship('PurchaseOrder', backref='container_transactions')
    customer = db.relationship('Customer', backref='container_transactions')

    def __repr__(self):
        return f"<ContainerTransaction {self.transaction_type} {self.quantity} of Container {self.container_id}>"

    def calculate_total_value(self):
        self.total_value = self.quantity * self.unit_value
        return self.total_value


class ProductUnit(db.Model, StatusMixin):
    __tablename__ = 'product_unit'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    # Name of the unit (Bottle, Dozen, Crate, etc.)
    unit_name = db.Column(db.String(50), nullable=False)

    # How many base units this represents (e.g., 1 crate = 12 bottles)
    conversion_quantity = db.Column(db.Integer, default=1, nullable=False)

    # Prices specific to this unit
    retail_price = db.Column(db.Float, default=0.0)
    wholesale_price = db.Column(db.Float, default=0.0)
    cost_price = db.Column(db.Float, default=0.0)

    # Whether the unit is refundable (e.g., crates or bottles that can be returned)
    is_returnable = db.Column(db.Boolean, default=False)

    # Optional barcode or code unique per unit
    unit_code = db.Column(db.String(50), unique=False,nullable=True)

    # Relationships
    product = db.relationship(
        'Product', 
        backref=db.backref('units', lazy=True, cascade="all, delete-orphan")
    )

    # Link back to ReturnableContainers
    containers = db.relationship('ReturnableContainer', back_populates='product_unit', lazy=True)

    def __repr__(self):
        return f"<ProductUnit {self.unit_name} of {self.product.name}>"

    def get_total_price(self, quantity):
        """Calculate total retail value for given quantity."""
        return self.retail_price * quantity


class CustomerDebt(db.Model, StatusMixin):
    __tablename__ = 'customer_debt'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=True)

    # Financials
    debt_balance = db.Column(db.Float, nullable=False, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    amount_paid = db.Column(db.Float, default=0.0)

    # Tracking & Description
    memo = db.Column(db.String(255))
    debt_date = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'), nullable=True)

    # Status: "Pending", "Partial", "Cleared"
    payment_status = db.Column(db.String(20), default="Pending")

    # Relationships
    customer = db.relationship('Customer', backref=db.backref('debts', lazy=True))
    sale = db.relationship('Sale', backref=db.backref('customer_debt', uselist=False))
    transaction_number = db.relationship('TransactionNumber')

    def update_status(self):
        """Automatically update status based on payments."""
        if self.amount_paid >= self.total_amount:
            self.payment_status = "Cleared"
            self.debt_balance = 0
        elif self.amount_paid > 0:
            self.payment_status = "Partial"
            self.debt_balance = self.total_amount - self.amount_paid
        else:
            self.payment_status = "Pending"

        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f"<CustomerDebt Customer={self.customer_id} Balance={self.debt_balance}>"



class CustomerPayment(db.Model, StatusMixin):
    __tablename__ = 'customer_payment'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=True)
    debt_id = db.Column(db.Integer, db.ForeignKey('customer_debt.id'), nullable=True)

    # Payment info
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    payment_type = db.Column(db.String(20), default='Cash')  # Cash, Bank, MobileMoney
    reference = db.Column(db.String(100))
    transaction_no = db.Column(db.Integer, db.ForeignKey('transaction_number.id'), nullable=True)

    # Status
    status = db.Column(db.String(20), default="Completed")  # Pending, Completed, Reversed

    # Relationships
    customer = db.relationship('Customer', backref=db.backref('payments', lazy=True))
    sale = db.relationship('Sale', backref=db.backref('payments', lazy=True))
    debt = db.relationship('CustomerDebt', backref=db.backref('payments', lazy=True))
    payment_account = db.relationship('Account', backref=db.backref('customer_payments', lazy=True))
    transaction_number = db.relationship('TransactionNumber')

    def __repr__(self):
        return f"<CustomerPayment {self.amount} from Customer={self.customer_id}>"
