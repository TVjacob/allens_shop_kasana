from flask import Blueprint, request, jsonify
from app import db
from app.models import GeneralLedger, Account
from datetime import datetime

from app.utils.auth import token_required

ledger_bp = Blueprint('ledger', __name__, url_prefix='/ledger')

# --- Add a transaction ---
@token_required
@ledger_bp.route('/', methods=['POST'])
def add_transaction():
    data = request.json
    account = Account.query.filter_by(id=data['account_id'], status=1).first()
    if not account:
        return jsonify({"error": "Active account not found"}), 404

    entry = GeneralLedger(
        account_id=account.id,
        transaction_type=data['transaction_type'],
        amount=data['amount'],
        description=data.get('description'),
        transaction_date=data.get('transaction_date', datetime.utcnow()),
        status=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"message": "Transaction recorded", "entry_id": entry.id})


# --- Get all ledger entries ---
@token_required
@ledger_bp.route('/', methods=['GET'])
def get_ledger():
    entries = GeneralLedger.query.all()
    data = []
    for e in entries:
        account = Account.query.get(e.account_id)
        data.append({
            "entry_id": e.id,
            "account_name": account.name if account else None,
            "transaction_type": e.transaction_type,
            "amount": e.amount,
            "description": e.description,
            "transaction_date": e.transaction_date,
            "status": e.status,
            "created_at": e.created_at,
            "updated_at": e.updated_at
        })
    return jsonify(data)


# --- Get ledger by account ---
@token_required
@ledger_bp.route('/account/<int:account_id>', methods=['GET'])
def get_ledger_by_account(account_id):
    account = Account.query.filter_by(id=account_id, status=1).first_or_404()
    entries = GeneralLedger.query.filter_by(account_id=account_id).all()
    data = [{
        "entry_id": e.id,
        "transaction_type": e.transaction_type,
        "amount": e.amount,
        "description": e.description,
        "transaction_date": e.transaction_date,
        "status": e.status,
        "created_at": e.created_at,
        "updated_at": e.updated_at
    } for e in entries]
    return jsonify({"account": account.name, "entries": data})


# --- Update ledger entry ---
@token_required
@ledger_bp.route('/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    entry = GeneralLedger.query.get_or_404(entry_id)
    data = request.json
    if "account_id" in data:
        account = Account.query.filter_by(id=data['account_id'], status=1).first()
        if not account:
            return jsonify({"error": "Active account not found"}), 404
        entry.account_id = account.id

    entry.transaction_type = data.get('transaction_type', entry.transaction_type)
    entry.amount = data.get('amount', entry.amount)
    entry.description = data.get('description', entry.description)
    entry.transaction_date = data.get('transaction_date', entry.transaction_date)
    entry.updated_at = datetime.utcnow()
    entry.status = 1
    db.session.commit()
    return jsonify({"message": "Transaction updated", "entry_id": entry.id})


# --- Delete ledger entry (soft delete) ---
@token_required
@ledger_bp.route('/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    entry = GeneralLedger.query.get_or_404(entry_id)
    entry.status = 0
    entry.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Transaction marked inactive", "entry_id": entry_id})
