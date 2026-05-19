from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.product import Product, Category
from app.models.order import OrderItem, Order

seller_bp = Blueprint("seller", __name__, url_prefix="/seller")


def seller_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "seller":
            flash("Seller access required.", "danger")
            return redirect(url_for("products.index"))
        return f(*args, **kwargs)
    return decorated


def approved_seller_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "seller":
            flash("Seller access required.", "danger")
            return redirect(url_for("products.index"))
        # BR-2: only approved sellers may publish products
        if not current_user.is_approved_seller():
            flash("Your account is pending administrator approval (BR-2).", "warning")
            return redirect(url_for("seller.dashboard"))
        return f(*args, **kwargs)
    return decorated


@seller_bp.route("/dashboard")
@login_required
@seller_required
def dashboard():
    products = []
    if current_user.seller_profile:
        products = Product.query.filter_by(
            seller_id=current_user.seller_profile.seller_id
        ).order_by(Product.product_id.desc()).all()
    return render_template("seller/dashboard.html", products=products)


@seller_bp.route("/sales")
@login_required
@seller_required
def sales():
    orders_data = []
    if current_user.seller_profile:
        orders = db.session.query(Order).join(OrderItem).join(Product).filter(
            Product.seller_id == current_user.seller_profile.seller_id
        ).distinct().order_by(Order.order_date.desc()).all()
        
        for order in orders:
            seller_items = [
                item for item in order.items
                if item.product.seller_id == current_user.seller_profile.seller_id
            ]
            if seller_items:
                seller_total = sum(item.get_subtotal() for item in seller_items)
                orders_data.append({
                    'order': order,
                    'order_items': seller_items,
                    'seller_total': seller_total
                })
    
    return render_template("seller/sales.html", orders_data=orders_data)


@seller_bp.route("/products/add", methods=["GET", "POST"])
@login_required
@approved_seller_required
def add_product():
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", type=float)
        stock = request.form.get("stock_quantity", type=int)
        category_id = request.form.get("category_id", type=int)

        if not name or price is None or stock is None or not category_id:
            flash("All fields are required.", "danger")
            return render_template("seller/add_product.html", categories=categories)

        if price <= 0:
            flash("Price must be greater than 0.", "danger")
            return render_template("seller/add_product.html", categories=categories)

        if stock < 0:
            flash("Stock quantity cannot be negative.", "danger")
            return render_template("seller/add_product.html", categories=categories)

        product = Product(
            name=name,
            description=description,
            price=price,
            stock_quantity=stock,
            seller_id=current_user.seller_profile.seller_id,
            category_id=category_id,
            is_active=1,
        )
        db.session.add(product)
        db.session.commit()
        flash(f"'{name}' has been listed in the catalog.", "success")
        return redirect(url_for("seller.dashboard"))

    return render_template("seller/add_product.html", categories=categories)


@seller_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@approved_seller_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.seller_id != current_user.seller_profile.seller_id:
        flash("You can only edit your own products.", "danger")
        return redirect(url_for("seller.dashboard"))

    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", type=float)
        stock = request.form.get("stock_quantity", type=int)
        category_id = request.form.get("category_id", type=int)
        is_active = 1 if request.form.get("is_active") else 0

        if not name or price is None or stock is None or not category_id:
            flash("All fields are required.", "danger")
            return render_template("seller/edit_product.html",
                                   product=product, categories=categories)

        if price <= 0:
            flash("Price must be greater than 0.", "danger")
            return render_template("seller/edit_product.html",
                                   product=product, categories=categories)

        if stock < 0:
            flash("Stock cannot be negative (BR-3).", "danger")
            return render_template("seller/edit_product.html",
                                   product=product, categories=categories)

        product.name = name
        product.description = description
        product.price = price
        product.stock_quantity = stock
        product.category_id = category_id
        product.is_active = is_active

        db.session.commit()
        flash("Product updated successfully.", "success")
        return redirect(url_for("seller.dashboard"))

    return render_template("seller/edit_product.html",
                           product=product, categories=categories)


@seller_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
@approved_seller_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.seller_id != current_user.seller_profile.seller_id:
        flash("You can only delete your own products.", "danger")
        return redirect(url_for("seller.dashboard"))

    product.is_active = 0  # Soft delete — FR-10
    db.session.commit()
    flash(f"'{product.name}' has been removed from the catalog.", "info")
    return redirect(url_for("seller.dashboard"))
