from app import db
from app.models import GeneralLedger, ProductUnit, PurchaseOrder, PurchaseOrderItem, TransactionNumber, Account
from datetime import datetime
from sqlalchemy import cast, Integer
from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.orm import aliased
from datetime import datetime
from sqlalchemy import and_


def post_to_ledger(entries, transaction_no_id, description=None, transaction_date=None):
    if transaction_date is None:
        transaction_date = datetime.utcnow()

    # Convert all account codes to strings
    account_codes = {str(e['account_id']) for e in entries}

    # Fetch accounts once
    accounts = (
        db.session.query(Account.code, Account.id)
        .filter(cast(Account.code, Integer).in_(account_codes))
        .all()
    )
    account_lookup = {str(code): id for code, id in accounts}

    gl_entries = []
    for e in entries:
        code = str(e['account_id'])
        if code not in account_lookup:
            raise ValueError(f"Account with code {code} not found.")
        print(f"Posting to GL: Account Code={code}, Type={e['transaction_type']}, Amount={e['amount']}")

        # Create GL entry and populate StatusMixin fields
        gl_entry = GeneralLedger(
            account_id=account_lookup[code],
            transaction_type=e['transaction_type'],
            amount=e['amount'],
            description=description,
            transaction_date=transaction_date,
            transaction_no=transaction_no_id,
            status=1,  # Active
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.session.add(gl_entry)
        gl_entries.append(gl_entry)

    db.session.commit()
    return gl_entries



from sqlalchemy.orm import aliased



def get_latest_purchase_price_no_rounds(product_id, unit_id=None, up_to_date=None):
    """
    Get the latest purchase price for a given product and optional unit and date.
    Uses INNER JOIN with ProductUnit and conversion_quantity for proper unit price conversion.
    """
    print("unit_id:", unit_id)

    # Alias ProductUnit
    # Unit = aliased(ProductUnit)

    # Build query using INNER JOIN with ProductUnit
    query = (
        db.session.query(PurchaseOrderItem, ProductUnit.conversion_quantity)
        .join(ProductUnit, ProductUnit.id == PurchaseOrderItem.unit_id)
        .filter(
            PurchaseOrderItem.product_id == product_id,
            PurchaseOrderItem.status == 1
        )
    )

    # Filter by date if provided
    if up_to_date:
        query = query.join(PurchaseOrder).filter(PurchaseOrder.purchase_date <= up_to_date)

    # Try exact unit match first
    if unit_id:
        result = (
            query.filter(PurchaseOrderItem.unit_id == unit_id)
            .order_by(PurchaseOrderItem.created_at.desc())
            .first()
        )
        if result:
            purchase_item, conversion_quantity = result
            print(" cont converted sales ", conversion_quantity)
            return round(purchase_item.unit_price, 2) ,True

    # Fallback: latest purchase for any unit
    result = query.order_by(PurchaseOrderItem.created_at.desc()).first()
    if not result:
        return 0.0

    purchase_item, conversion_quantity = result
    
    if conversion_quantity and conversion_quantity > 0:
        print(" flase s converted sales ", conversion_quantity)
        return purchase_item.unit_price / conversion_quantity , False
    print(" conversion_quantity  converted sales ", conversion_quantity)
    return purchase_item.unit_price ,False

def get_latest_purchase_price(product_id, unit_id=None, up_to_date=None):
    """
    Get the latest purchase price for a given product and optional unit and date.
    Uses INNER JOIN with ProductUnit and conversion_quantity for proper unit price conversion.
    """
    print("unit_id:", unit_id)

    # Alias ProductUnit
    # Unit = aliased(ProductUnit)

    # Build query using INNER JOIN with ProductUnit
    query = (
        db.session.query(PurchaseOrderItem, ProductUnit.conversion_quantity)
        .join(ProductUnit, ProductUnit.id == PurchaseOrderItem.unit_id)
        .filter(
            PurchaseOrderItem.product_id == product_id,
            PurchaseOrderItem.status == 1
        )
    )

    # Filter by date if provided
    if up_to_date:
        query = query.join(PurchaseOrder).filter(PurchaseOrder.purchase_date <= up_to_date)

    # Try exact unit match first
    if unit_id:
        result = (
            query.filter(PurchaseOrderItem.unit_id == unit_id)
            .order_by(PurchaseOrderItem.created_at.desc())
            .first()
        )
        if result:
            purchase_item, conversion_quantity = result
            # Apply conversion
            # if conversion_quantity and conversion_quantity > 0:
            #     return round(purchase_item.unit_price / conversion_quantity, 2)
            return round(purchase_item.unit_price, 2)

    # Fallback: latest purchase for any unit
    result = query.order_by(PurchaseOrderItem.created_at.desc()).first()
    if not result:
        return 0.0

    purchase_item, conversion_quantity = result
    
    if conversion_quantity and conversion_quantity > 0:
        return round(purchase_item.unit_price / conversion_quantity, 2)
    return round(purchase_item.unit_price, 2)


# def get_latest_purchase_price(product_id, unit_id=None, up_to_date=None):
#     """
#     Get the latest purchase price for a given product and optional unit and date.
#     If no exact match for the unit is found, falls back to the product's last purchase price.
#     If a conversion unit exists, the price is adjusted based on its conversion quantity.
#     """
#     print("unit_id:", unit_id)

#     # Build initial query for this product

#     # Optional: alias the ProductUnit table for clarity
#     Unit = aliased(ProductUnit)

#     query = (
#         db.session.query(PurchaseOrderItem, Unit)
#         .join(Unit, Unit.id == PurchaseOrderItem.unit_id)
#         .filter(
#             PurchaseOrderItem.product_id == product_id,
#             PurchaseOrderItem.status == 1
#         )
#     )


#     # Filter by date if provided
#     if up_to_date:
#         query = query.join(PurchaseOrder).filter(PurchaseOrder.purchase_date <= up_to_date)

#     # Try to get latest purchase for exact unit first
#     if unit_id:
#         latest_purchase = (
#             query.filter(PurchaseOrderItem.unit_id == unit_id)
#             .order_by(PurchaseOrderItem.created_at.desc())
#             .first()
#         )
#         if latest_purchase:
#             return latest_purchase.unit_price

#     # Fallback: get the most recent purchase for the product (any unit)
#     latest_purchase = query.order_by(PurchaseOrderItem.created_at.desc()).first()
#     if not latest_purchase:
#         return 0.0  # No purchase history at all

#     # Get the conversion quantity for the requested unit
#     unit = None
#     if unit_id:
#         unit = ProductUnit.query.filter_by(id=unit_id, product_id=product_id).first()

#     print(" unit ", unit)

#     # If no unit_id given, try to get smallest conversion unit for the product
#     if not unit:
#         unit = (
#             ProductUnit.query
#             .filter_by(product_id=product_id)
#             .order_by(ProductUnit.conversion_quantity.asc())
#             .first()
#         )
        
#     print(" unit ",unit)

#     # Adjust for conversion if possible
#     if unit and unit.conversion_quantity > 0:
#         print(" unit ", unit.conversion_quantity)
#         return round(latest_purchase.unit_price / unit.conversion_quantity, 2)

#     # Otherwise, return the base price
#     return round(latest_purchase.unit_price, 2)


# def get_latest_purchase_price(product_id, unit_id=None, up_to_date=None):
#     """
#     Get the latest purchase price for a given product and (optional) unit and date.
#     If no exact match for the unit is found, falls back to the product's last purchase price.
#     If a conversion unit exists, convert price accordingly.

#     Args:
#         product_id (int): Product ID to look up.
#         unit_id (int, optional): Unit ID. If None, will still attempt conversion if unit exists.
#         up_to_date (datetime, optional): Only consider purchases before this date.

#     Returns:
#         float: Latest purchase price for that product/unit (converted if applicable).
#     """
#     query = PurchaseOrderItem.query.filter(
#         PurchaseOrderItem.product_id == product_id,
#         PurchaseOrderItem.status == 1,
        
#     ).join(ProductUnit, ProductUnit.id == PurchaseOrderItem.unit_id)

#     # Filter by date if provided
#     if up_to_date:
#         query = query.join(PurchaseOrder).filter(PurchaseOrder.purchase_date <= up_to_date)

#     # Try exact match for unit first
#     if unit_id:
#         latest_purchase = (
#             query.filter(PurchaseOrderItem.unit_id == unit_id)
#             .order_by(PurchaseOrderItem.created_at.desc())
#             .first()
#         )
#         if latest_purchase:
#             return latest_purchase.unit_price
    
    

#     # Otherwise, get fallback purchase (base unit)
#     fallback_purchase = query.order_by(PurchaseOrderItem.created_at.desc()).first()
#     if not fallback_purchase:
#         return 0.0  # No purchase history


#     if unit and unit.conversion_quantity > 0:
#         return fallback_purchase.unit_price / unit.conversion_quantity

#     # Otherwise return fallback base price
#     return fallback_purchase.unit_price


# def get_lastest(product_id, unit=None,up_to_date=None):
#     latest_purchase = (PurchaseOrderItem.query .filter(PurchaseOrderItem.product_id == product.id, PurchaseOrderItem.unit_id == unit_id) .order_by(PurchaseOrderItem.created_at.desc()) .first())

#     query = PurchaseOrderItem.query.filter(
#         PurchaseOrderItem.product_id == product_id,
#         PurchaseOrderItem.status == 1
#     )





# def generate_transaction_number(prefix, transaction_date=None, status=1):
#     # ✅ Generate a fresh timestamp each time
#     if transaction_date is None:
#         transaction_date = datetime.utcnow()

#     tn = TransactionNumber.query.filter_by(prefix=prefix).first()

#     if not tn:
#         tn = TransactionNumber(
#             prefix=prefix,
#             last_number=1,
#             status=status,
#             transaction_date=transaction_date
#         )
#         db.session.add(tn)
#         db.session.commit()
#     else:
#         tn.last_number += 1
#         db.session.commit()

#     txn_str = f"{prefix}-{str(tn.last_number).zfill(5)}"
#     return tn.id, txn_str


def generate_transaction_number(prefix, transaction_date=None, status=1):
    if transaction_date is None:
        transaction_date = datetime.utcnow()

    # tn = TransactionNumber.query.filter_by(prefix=prefix).first()

    # if not tn:
    tn = TransactionNumber(
        prefix=prefix,
        last_number=1,
        status=status,
        transaction_date=transaction_date
    )
    db.session.add(tn)
    db.session.flush()  # <-- Ensure ID is available before commit
    # else:
    #     tn.last_number += 1
    #     db.session.flush()

    txn_str = f"{prefix}-{str(tn.id).zfill(5)}"

    db.session.commit()  # <-- Final commit
    return tn.id, txn_str


def generate_transaction_number_partone(prefix, transaction_date=None, status=1):
    if transaction_date is None:
        transaction_date = datetime.utcnow()

    # tn = TransactionNumber.query.filter_by(prefix=prefix).first()

    # if not tn:
    tn = TransactionNumber(
        prefix=prefix,
        last_number=1,
        status=status,
        transaction_date=transaction_date
    )
    db.session.add(tn)
    db.session.flush()  # <-- Ensure ID is available before commit
    # else:
    #     tn.last_number += 1
    #     db.session.flush()

    txn_str = f"{prefix}-{str(tn.id).zfill(5)}"

    db.session.commit()  # <-- Final commit
    return tn.id, txn_str

