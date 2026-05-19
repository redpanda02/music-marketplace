from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import User, Seller
from app.models.product import Product, Category
from app.models.order import Order

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Administrator access required.", "danger")
            return redirect(url_for("products.index"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    pending_sellers = Seller.query.filter_by(is_approved=0).count()
    return render_template("admin/dashboard.html",
                           total_users=total_users,
                           total_products=total_products,
                           total_orders=total_orders,
                           pending_sellers=pending_sellers)


# ── Seller Management ────────────────────────────────────────────────────────

@admin_bp.route("/sellers")
@login_required
@admin_required
def sellers():
    all_sellers = Seller.query.join(User).order_by(Seller.is_approved).all()
    return render_template("admin/sellers.html", sellers=all_sellers)


@admin_bp.route("/sellers/<int:seller_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_seller(seller_id):
    """UC-08: Approve Seller — BR-2."""
    seller = Seller.query.get_or_404(seller_id)
    seller.approve()
    db.session.commit()
    flash(f"Seller '{seller.user.name}' has been approved.", "success")
    return redirect(url_for("admin.sellers"))


@admin_bp.route("/sellers/<int:seller_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_seller(seller_id):
    seller = Seller.query.get_or_404(seller_id)
    seller.reject()
    db.session.commit()
    flash(f"Seller '{seller.user.name}' has been rejected.", "warning")
    return redirect(url_for("admin.sellers"))


# ── Category Management ──────────────────────────────────────────────────────

@admin_bp.route("/categories")
@login_required
@admin_required
def categories():
    all_categories = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", categories=all_categories)


@admin_bp.route("/categories/add", methods=["POST"])
@login_required
@admin_required
def add_category():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Category name is required.", "danger")
        return redirect(url_for("admin.categories"))

    if Category.query.filter_by(name=name).first():
        flash("Category already exists.", "warning")
        return redirect(url_for("admin.categories"))

    db.session.add(Category(name=name))
    db.session.commit()
    flash(f"Category '{name}' created.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    # UC-09 alternate flow: cannot delete if products exist
    if category.products:
        flash(f"Cannot delete '{category.name}' — it still contains products.", "danger")
        return redirect(url_for("admin.categories"))

    db.session.delete(category)
    db.session.commit()
    flash(f"Category '{category.name}' deleted.", "info")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:category_id>/rename", methods=["POST"])
@login_required
@admin_required
def rename_category(category_id):
    category = Category.query.get_or_404(category_id)
    new_name = request.form.get("name", "").strip()
    if not new_name:
        flash("Category name cannot be empty.", "danger")
        return redirect(url_for("admin.categories"))
    category.name = new_name
    db.session.commit()
    flash("Category renamed.", "success")
    return redirect(url_for("admin.categories"))


# ── User Management ──────────────────────────────────────────────────────────

@admin_bp.route("/users")
@login_required
@admin_required
def users():
    """BR-6: only admin manages user accounts."""
    all_users = User.query.order_by(User.role, User.name).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/remove", methods=["POST"])
@login_required
@admin_required
def remove_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin():
        flash("Cannot remove an administrator account.", "danger")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.name}' has been removed.", "info")
    return redirect(url_for("admin.users"))


# ── Product Oversight ────────────────────────────────────────────────────────

@admin_bp.route("/products")
@login_required
@admin_required
def products():
    all_products = Product.query.order_by(Product.product_id.desc()).all()
    return render_template("admin/products.html", products=all_products)


@admin_bp.route("/products/<int:product_id>/deactivate", methods=["POST"])
@login_required
@admin_required
def deactivate_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = 0
    db.session.commit()
    flash(f"Product '{product.name}' deactivated.", "info")
    return redirect(url_for("admin.products"))
