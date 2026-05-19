from app import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = "order"

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.Text, nullable=False,
                           default=lambda: datetime.utcnow().isoformat())
    status = db.Column(db.Text, nullable=False, default="pending")
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    customer_id = db.Column(db.Integer, db.ForeignKey("user.user_id"),
                            nullable=False)

    customer = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order",
                            cascade="all, delete-orphan")

    @staticmethod
    def place_order(cart):
        """
        Core order placement logic — realizes UC-05 Place Order.
        Enforces BR-1, BR-3, BR-4, BR-5.
        Returns (order, error_message).
        """
        # BR-5: cart must not be empty
        if cart.is_empty():
            return None, "Your cart is empty (BR-5)."

        # BR-1: validate stock for all items before doing anything
        for cart_item in cart.items:
            product = cart_item.product
            if not product.is_available():
                return None, f"'{product.name}' is no longer available."
            if cart_item.quantity > product.stock_quantity:
                return None, (
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {product.stock_quantity}, "
                    f"Requested: {cart_item.quantity} (BR-1)."
                )

        # All validations passed — create order
        order = Order(customer_id=cart.customer_id)
        db.session.add(order)
        db.session.flush()  # get order_id before adding items

        total = 0.0
        for cart_item in cart.items:
            product = cart_item.product

            # Snapshot price at time of purchase
            order_item = OrderItem(
                order_id=order.order_id,
                product_id=product.product_id,
                quantity=cart_item.quantity,
                price=product.price,
            )
            db.session.add(order_item)

            # BR-3: reduce stock (enforced in model)
            product.update_stock(cart_item.quantity)
            total += order_item.get_subtotal()

        order.total_amount = total
        order.status = "confirmed"

        # BR-4: order is recorded permanently — cart is cleared, not order
        cart.clear()

        return order, None

    def get_status(self):
        return self.status

    def cancel_order(self):
        """Cancel if still in cancellable state."""
        if self.status in ("pending", "confirmed"):
            self.status = "cancelled"
            return True
        return False

    def simulate_payment(self, payment_method):
        """Payment simulation — real gateway out of scope."""
        if self.status == "confirmed":
            self.status = "shipped"
            return True
        return False

    def __repr__(self):
        return f"<Order {self.order_id} [{self.status}]>"


class OrderItem(db.Model):
    __tablename__ = "order_item"

    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)   # snapshot at purchase time
    order_id = db.Column(db.Integer, db.ForeignKey("order.order_id"),
                         nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"),
                           nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

    def get_subtotal(self):
        return self.quantity * self.price

    def __repr__(self):
        return f"<OrderItem product={self.product_id} qty={self.quantity}>"
