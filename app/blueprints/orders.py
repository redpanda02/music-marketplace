from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.order import Order
from app.services import OrderService

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    """
    UC-05: Place Order — delegates to OrderService.place_order_atomic()
    Implements: Technical Recommendation #2 - Atomic transaction handling
    """
    if current_user.role != "customer":
        flash("Only customers can place orders.", "warning")
        return redirect(url_for("products.index"))

    cart = current_user.cart
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart.view"))

    order, error, success = OrderService.place_order_atomic(cart, current_user.user_id)

    if not success:
        flash(error, "danger")
        return redirect(url_for("cart.view"))

    flash(f"Order #{order.order_id} confirmed successfully!", "success")
    return redirect(url_for("orders.detail", order_id=order.order_id))


@orders_bp.route("/<int:order_id>")
@login_required
def detail(order_id):
    order = OrderService.get_order_by_id(order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("products.index"))
    
    if order.customer_id != current_user.user_id and not current_user.is_admin():
        flash("Access denied.", "danger")
        return redirect(url_for("products.index"))
    return render_template("orders/detail.html", order=order)


@orders_bp.route("/history")
@login_required
def history():
    """BR-4: order history preserved after completion or cancellation."""
    orders = OrderService.get_user_orders(current_user.user_id)
    return render_template("orders/history.html", orders=orders)


@orders_bp.route("/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel(order_id):
    order = OrderService.get_order_by_id(order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("orders.history"))
    
    if order.customer_id != current_user.user_id:
        flash("Access denied.", "danger")
        return redirect(url_for("orders.history"))

    success, message = OrderService.cancel_order(order_id)
    if success:
        flash(message, "info")
    else:
        flash(message, "warning")

    return redirect(url_for("orders.detail", order_id=order_id))
