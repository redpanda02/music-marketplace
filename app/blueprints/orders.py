from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.order import Order

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    """UC-05: Place Order — delegates to Order.place_order()."""
    if current_user.role != "customer":
        flash("Only customers can place orders.", "warning")
        return redirect(url_for("products.index"))

    cart = current_user.cart
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart.view"))

    order, error = Order.place_order(cart)

    if error:
        flash(error, "danger")
        return redirect(url_for("cart.view"))

    db.session.commit()
    flash(f"Order #{order.order_id} confirmed successfully!", "success")
    return redirect(url_for("orders.detail", order_id=order.order_id))


@orders_bp.route("/<int:order_id>")
@login_required
def detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.user_id and not current_user.is_admin():
        flash("Access denied.", "danger")
        return redirect(url_for("products.index"))
    return render_template("orders/detail.html", order=order)


@orders_bp.route("/history")
@login_required
def history():
    """BR-4: order history preserved after completion or cancellation."""
    orders = Order.query.filter_by(
        customer_id=current_user.user_id
    ).order_by(Order.order_id.desc()).all()
    return render_template("orders/history.html", orders=orders)


@orders_bp.route("/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.user_id:
        flash("Access denied.", "danger")
        return redirect(url_for("orders.history"))

    if order.cancel_order():
        db.session.commit()
        flash(f"Order #{order_id} has been cancelled.", "info")
    else:
        flash("This order cannot be cancelled.", "warning")

    return redirect(url_for("orders.detail", order_id=order_id))
