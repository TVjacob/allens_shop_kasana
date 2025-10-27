from app import db
from app.models import GeneralLedger, TransactionNumber, Account
from datetime import datetime
from sqlalchemy import cast, Integer


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

    tn = TransactionNumber.query.filter_by(prefix=prefix).first()

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

    txn_str = f"{prefix}-{str(tn.last_number).zfill(5)}"

    db.session.commit()  # <-- Final commit
    return tn.id, txn_str


def generate_transaction_number_partone(prefix, transaction_date=None, status=1):
    if transaction_date is None:
        transaction_date = datetime.utcnow()

    tn = TransactionNumber.query.filter_by(prefix=prefix).first()

    if not tn:
        tn = TransactionNumber(
            prefix=prefix,
            last_number=1,
            status=status,
            transaction_date=transaction_date
        )
        db.session.add(tn)
        db.session.flush()  # <-- ensure ID is available
    else:
        tn.last_number += 1
        db.session.flush()

    txn_str = f"{prefix}-{str(tn.last_number).zfill(5)}"

    return tn.id, txn_str

