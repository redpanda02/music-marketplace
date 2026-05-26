from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-fallback")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        app.instance_path, "marketplace.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import all models to register with SQLAlchemy
    from app.models.audit import AuditLog
    from app.models.product import Product, Category
    from app.models.order import Order, OrderItem
    from app.models.cart import Cart, CartItem

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.products import products_bp
    from app.blueprints.cart import cart_bp
    from app.blueprints.orders import orders_bp
    from app.blueprints.seller import seller_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(seller_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    """Seed initial admin account, categories, sellers, and sample products."""
    from app.models.user import User, Seller
    from app.models.product import Category, Product
    import bcrypt

    if not User.query.filter_by(email="admin@marketplace.com").first():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        admin = User(name="Admin", email="admin@marketplace.com",
                     password=hashed, role="admin")
        db.session.add(admin)

    categories = ["Guitars", "Drums", "Keyboards", "Wind Instruments",
                  "Bass", "Accessories", "Amplifiers", "Recording Gear"]
    from app.models.product import Category
    for name in categories:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))

    db.session.commit()

    # Create mock sellers
    sellers_data = [
        {"email": "seller1@marketplace.com", "name": "GuitarPro Store"},
        {"email": "seller2@marketplace.com", "name": "DrumMaster Shop"},
        {"email": "seller3@marketplace.com", "name": "Keyboard Kingdom"},
    ]

    sellers = []
    for seller_info in sellers_data:
        seller_user = User.query.filter_by(email=seller_info["email"]).first()
        if not seller_user:
            hashed = bcrypt.hashpw("seller123".encode(), bcrypt.gensalt()).decode()
            seller_user = User(name=seller_info["name"], email=seller_info["email"],
                              password=hashed, role="seller")
            db.session.add(seller_user)
            db.session.flush()
        if not seller_user.seller_profile:
            seller_profile = Seller(seller_id=seller_user.user_id, is_approved=1)
            db.session.add(seller_profile)
        sellers.append(seller_user)

    db.session.commit()

    # Create mock products
    mock_products = [
        # Guitars
        {"name": "Fender Stratocaster", "category": "Guitars", "seller_idx": 0,
         "description": "Classic electric guitar with versatile tone", "price": 799.99, "stock": 15},
        {"name": "Gibson Les Paul", "category": "Guitars", "seller_idx": 0,
         "description": "Iconic solid-body guitar with rich warmth", "price": 1299.99, "stock": 8},
        {"name": "Ibanez RG420", "category": "Guitars", "seller_idx": 0,
         "description": "Lightweight shredder guitar", "price": 449.99, "stock": 20},
        {"name": "Acoustic Dreadnought", "category": "Guitars", "seller_idx": 0,
         "description": "Perfect for songwriting and live performances", "price": 349.99, "stock": 12},

        # Drums
        {"name": "Pearl Export Drum Kit", "category": "Drums", "seller_idx": 1,
         "description": "5-piece drum kit, great for beginners and professionals", "price": 599.99, "stock": 10},
        {"name": "Ludwig Classic Maple", "category": "Drums", "seller_idx": 1,
         "description": "Premium 4-piece drum set with legendary sound", "price": 1899.99, "stock": 5},
        {"name": "Drum Throne", "category": "Drums", "seller_idx": 1,
         "description": "Comfortable and adjustable drum seat", "price": 79.99, "stock": 30},
        {"name": "Cymbal Pack", "category": "Drums", "seller_idx": 1,
         "description": "14-inch hi-hats, 16-inch crash, 20-inch ride", "price": 299.99, "stock": 18},

        # Keyboards
        {"name": "Yamaha P-125 Digital Piano", "category": "Keyboards", "seller_idx": 2,
         "description": "88 weighted keys with realistic grand piano touch", "price": 599.99, "stock": 14},
        {"name": "Korg Kross 2", "category": "Keyboards", "seller_idx": 2,
         "description": "Workstation keyboard with powerful synthesis", "price": 1499.99, "stock": 7},
        {"name": "Casio CTK-3500", "category": "Keyboards", "seller_idx": 2,
         "description": "Portable keyboard with 660 tones and rhythms", "price": 199.99, "stock": 25},

        # Bass
        {"name": "Fender Precision Bass", "category": "Bass", "seller_idx": 0,
         "description": "The foundation of modern bass guitar design", "price": 899.99, "stock": 9},
        {"name": "Ibanez SR505", "category": "Bass", "seller_idx": 0,
         "description": "5-string bass with ultra-thin neck", "price": 649.99, "stock": 11},

        # Amplifiers
        {"name": "Marshall MG100HCFX", "category": "Amplifiers", "seller_idx": 1,
         "description": "100-watt guitar amplifier with effects", "price": 799.99, "stock": 8},
        {"name": "Orange Crush 35RT", "category": "Amplifiers", "seller_idx": 1,
         "description": "35-watt combo amp with warm tone", "price": 449.99, "stock": 13},
        {"name": "Ampeg SVT-7PRO", "category": "Amplifiers", "seller_idx": 1,
         "description": "Professional 1000-watt bass amplifier", "price": 1299.99, "stock": 4},

        # Accessories
        {"name": "Guitar Strings (12-pack)", "category": "Accessories", "seller_idx": 2,
         "description": "High-quality bronze acoustic strings", "price": 39.99, "stock": 50},
        {"name": "Guitar Capo", "category": "Accessories", "seller_idx": 2,
         "description": "Aluminum construction, works on all guitars", "price": 19.99, "stock": 40},
        {"name": "Guitar Cable (10ft)", "category": "Accessories", "seller_idx": 2,
         "description": "Shielded instrument cable with gold connectors", "price": 24.99, "stock": 60},
        {"name": "Violin Bow Rosin", "category": "Accessories", "seller_idx": 2,
         "description": "Professional grade rosin", "price": 12.99, "stock": 100},

        # Recording Gear
        {"name": "Audio Technica AT2020 Microphone", "category": "Recording Gear", "seller_idx": 1,
         "description": "Condenser microphone for studio and live", "price": 149.99, "stock": 16},
        {"name": "Scarlett 2i2 Audio Interface", "category": "Recording Gear", "seller_idx": 1,
         "description": "USB audio interface with 2 inputs and 2 outputs", "price": 179.99, "stock": 22},
        {"name": "Studio Monitor Stands (Pair)", "category": "Recording Gear", "seller_idx": 1,
         "description": "Isolation stands for studio monitors", "price": 89.99, "stock": 19},

        # Wind Instruments
        {"name": "Yamaha YAS-280 Alto Saxophone", "category": "Wind Instruments", "seller_idx": 0,
         "description": "Student alto sax with great tone quality", "price": 799.99, "stock": 6},
        {"name": "Trumpet Bb Lacquer", "category": "Wind Instruments", "seller_idx": 0,
         "description": "Professional quality trumpet with hard case", "price": 599.99, "stock": 10},
    ]

    for product_info in mock_products:
        if not Product.query.filter_by(name=product_info["name"]).first():
            category = Category.query.filter_by(name=product_info["category"]).first()
            seller = sellers[product_info["seller_idx"]]
            product = Product(
                name=product_info["name"],
                description=product_info["description"],
                price=product_info["price"],
                stock_quantity=product_info["stock"],
                seller_id=seller.seller_profile.seller_id,
                category_id=category.category_id,
                is_active=1
            )
            db.session.add(product)

    db.session.commit()
