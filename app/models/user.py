from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)  # bcrypt hash
    role = db.Column(db.Text, nullable=False)       # customer | seller | admin

    # Relationships
    seller_profile = db.relationship("Seller", back_populates="user",
                                     uselist=False, cascade="all, delete-orphan")
    cart = db.relationship("Cart", back_populates="customer",
                           uselist=False, cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="customer",
                             cascade="all, delete-orphan")

    def get_id(self):
        return str(self.user_id)

    def is_admin(self):
        return self.role == "admin"

    def is_seller(self):
        return self.role == "seller"

    def is_customer(self):
        return self.role == "customer"

    def is_approved_seller(self):
        return (self.role == "seller" and
                self.seller_profile is not None and
                self.seller_profile.is_approved)

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"


class Seller(db.Model):
    __tablename__ = "seller"

    seller_id = db.Column(db.Integer, db.ForeignKey("user.user_id"),
                          primary_key=True)
    is_approved = db.Column(db.Integer, nullable=False, default=0)  # BR-2
    
    # Seller reputation tracking (Technical Recommendation #4)
    total_sales = db.Column(db.Integer, nullable=False, default=0)
    total_rating = db.Column(db.Float, nullable=False, default=0.0)  # avg rating 0-5
    num_reviews = db.Column(db.Integer, nullable=False, default=0)
    joined_date = db.Column(db.Text)  # ISO format timestamp

    user = db.relationship("User", back_populates="seller_profile")
    products = db.relationship("Product", back_populates="seller",
                               cascade="all, delete-orphan")

    def approve(self):
        self.is_approved = 1

    def reject(self):
        self.is_approved = 0

    def __repr__(self):
        status = "approved" if self.is_approved else "pending"
        return f"<Seller {self.seller_id} [{status}]>"
