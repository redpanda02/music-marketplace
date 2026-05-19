from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.product import Product
from app.models.cart import Cart

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


def _get_or_create_cart():
    if current_user.cart:
        return current_user.cart
    cart = Cart(customer_id=current_user.user_id)
    db.session.add(cart)
    db.session.commit()
    return cart


@cart_bp.route("/")
@login_required
def view():
    cart = _get_or_create_cart()
    return render_template("cart/view.html", cart=cart)


@cart_bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def add(product_id):
    if current_user.role not in ("customer",):
        flash("Only customers can add items to cart.", "warning")
        return redirect(url_for("products.index"))

    product = Product.query.get_or_404(product_id)
    quantity = request.form.get("quantity", 1, type=int)

    if quantity < 1:
        flash("Quantity must be at least 1.", "danger")
        return redirect(url_for("products.detail", product_id=product_id))

    cart = _get_or_create_cart()

    try:
        cart.add_item(product, quantity)
        db.session.commit()
        flash(f"'{product.name}' added to cart.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("products.detail", product_id=product_id))


@cart_bp.route("/remove/<int:cart_item_id>", methods=["POST"])
@login_required
def remove(cart_item_id):
    cart = _get_or_create_cart()
    cart.remove_item(cart_item_id)
    db.session.commit()
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart.view"))


@cart_bp.route("/update/<int:cart_item_id>", methods=["POST"])
@login_required
def update(cart_item_id):
    quantity = request.form.get("quantity", 1, type=int)
    cart = _get_or_create_cart()
    try:
        cart.update_quantity(cart_item_id, quantity)
        db.session.commit()
        flash("Cart updated.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("cart.view"))
