from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    app.config["SECRET_KEY"] = "sjhardwaresecretkey"

    db.init_app(app)
    migrate.init_app(app, db)

    # ✅ Enable CORS for your Vue frontend and allow Authorization header
    # CORS(
    #     app,
    #     resources={r"/api/*": {"origins": "http://localhost:5173"}},
    #     supports_credentials=True,
    #     expose_headers=["Content-Type", "Authorization"],
    #     allow_headers=["Content-Type", "Authorization"]
    # )
#     CORS(
#     app,
#     resources={r"/api/*": {"origins": "http://localhost:5173"}},
#     supports_credentials=True,
#     expose_headers=["Content-Type", "Authorization"],
#     allow_headers=["Content-Type", "Authorization"]
# )
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5173","http://localhost:5174","/*"]}},  # Vue dev server
        supports_credentials=True,
        expose_headers=["Content-Type", "Authorization"],
        allow_headers=["Content-Type", "Authorization"]
    )
    # Import blueprints
    from app.routes.inventory import inventory_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.sales import sales_bp
    from app.routes.payments import payments_bp
    from app.routes.expenses import expenses_bp
    from app.routes.accounts import accounts_bp
    from app.routes.ledger import ledger_bp
    from app.routes.users import users_bp
    from app.routes.customer import customer_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.reports import reports_bp

    # Register blueprints
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')
    app.register_blueprint(sales_bp, url_prefix='/api/sales')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(expenses_bp, url_prefix='/api/expenses')
    app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
    app.register_blueprint(ledger_bp, url_prefix='/api/ledgers')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(customer_bp, url_prefix='/api/customer')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')

    return app
