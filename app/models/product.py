from app import db


class Category(db.Model):
    __tablename__ = "category"

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False, unique=True)

    products = db.relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    __tablename__ = "product"

    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)  # BR-3
    is_active = db.Column(db.Integer, nullable=False, default=1)        # FR-10
    seller_id = db.Column(db.Integer, db.ForeignKey("seller.seller_id"),
                          nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.category_id"),
                            nullable=False)

    seller = db.relationship("Seller", back_populates="products")
    category = db.relationship("Category", back_populates="products")
    order_items = db.relationship("OrderItem", back_populates="product")
    cart_items = db.relationship("CartItem", back_populates="product",
                                 cascade="all, delete-orphan")

    def is_available(self):
        """Check stock availability — used in sequence diagram validateStock."""
        return self.is_active == 1 and self.stock_quantity > 0

    def update_stock(self, quantity):
        """Reduce stock by quantity. Enforces BR-3: stock must remain >= 0."""
        if self.stock_quantity - quantity < 0:
            raise ValueError("Stock quantity cannot be negative (BR-3)")
        self.stock_quantity -= quantity

    def get_details(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "is_active": self.is_active,
            "category": self.category.name if self.category else None,
            "seller": self.seller.user.name if self.seller and self.seller.user else None,
        }

    def __repr__(self):
        return f"<Product {self.name} (stock={self.stock_quantity})>"
