from app import db
from datetime import datetime


class Cart(db.Model):
    __tablename__ = "cart"

    cart_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_date = db.Column(db.Text, nullable=False,
                             default=lambda: datetime.utcnow().isoformat())
    customer_id = db.Column(db.Integer, db.ForeignKey("user.user_id"),
                            nullable=False, unique=True)

    customer = db.relationship("User", back_populates="cart")
    items = db.relationship("CartItem", back_populates="cart",
                            cascade="all, delete-orphan")

    def add_item(self, product, quantity):
        """Add or update a cart item. Validates stock before adding."""
        if not product.is_available():
            raise ValueError("Product is not available.")
        if quantity > product.stock_quantity:
            raise ValueError("Requested quantity exceeds available stock (BR-1).")

        existing = CartItem.query.filter_by(
            cart_id=self.cart_id, product_id=product.product_id
        ).first()

        if existing:
            new_qty = existing.quantity + quantity
            if new_qty > product.stock_quantity:
                raise ValueError("Total quantity exceeds available stock (BR-1).")
            existing.quantity = new_qty
        else:
            item = CartItem(cart_id=self.cart_id,
                            product_id=product.product_id,
                            quantity=quantity)
            db.session.add(item)

    def remove_item(self, cart_item_id):
        item = CartItem.query.filter_by(
            cart_item_id=cart_item_id, cart_id=self.cart_id
        ).first()
        if item:
            db.session.delete(item)

    def update_quantity(self, cart_item_id, quantity):
        item = CartItem.query.filter_by(
            cart_item_id=cart_item_id, cart_id=self.cart_id
        ).first()
        if item:
            if quantity <= 0:
                db.session.delete(item)
            elif quantity > item.product.stock_quantity:
                raise ValueError("Quantity exceeds available stock (BR-1).")
            else:
                item.quantity = quantity

    def get_total(self):
        return sum(i.get_subtotal() for i in self.items)

    def clear(self):
        for item in self.items:
            db.session.delete(item)

    def is_empty(self):
        return len(self.items) == 0

    def __repr__(self):
        return f"<Cart {self.cart_id} ({len(self.items)} items)>"


class CartItem(db.Model):
    __tablename__ = "cart_item"

    cart_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quantity = db.Column(db.Integer, nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.cart_id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"),
                           nullable=False)

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product", back_populates="cart_items")

    def get_subtotal(self):
        return self.quantity * self.product.price

    def update_quantity(self, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        self.quantity = quantity

    def __repr__(self):
        return f"<CartItem product={self.product_id} qty={self.quantity}>"
