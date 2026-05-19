from flask import Blueprint, render_template, request
from app.models.product import Product, Category

products_bp = Blueprint("products", __name__, url_prefix="/")


@products_bp.route("/")
def index():
    """Home — product listing with optional search and category filter."""
    search = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)

    query = Product.query.filter_by(is_active=1)

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    if category_id:
        query = query.filter_by(category_id=category_id)

    products = query.order_by(Product.product_id.desc()).all()
    categories = Category.query.order_by(Category.name).all()

    return render_template(
        "products/index.html",
        products=products,
        categories=categories,
        search=search,
        selected_category=category_id,
    )


@products_bp.route("/products/<int:product_id>")
def detail(product_id):
    """Product detail page."""
    product = Product.query.get_or_404(product_id)
    return render_template("products/detail.html", product=product)
