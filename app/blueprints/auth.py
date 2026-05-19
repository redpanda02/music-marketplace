from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User, Seller
from app.models.cart import Cart
import bcrypt

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("products.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "customer")

        # Validate inputs
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("auth/register.html")

        if role not in ("customer", "seller"):
            role = "customer"

        # UC-01: check email uniqueness
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please use a different email.", "danger")
            return render_template("auth/register.html")

        # Create user
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(name=name, email=email, password=hashed, role=role)
        db.session.add(user)
        db.session.flush()

        if role == "seller":
            seller = Seller(seller_id=user.user_id, is_approved=0)
            db.session.add(seller)
        elif role == "customer":
            cart = Cart(customer_id=user.user_id)
            db.session.add(cart)

        db.session.commit()
        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("products.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        # UC-02: verify credentials
        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")

            # Redirect based on role
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif user.role == "seller":
                return redirect(url_for("seller.dashboard"))
            else:
                return redirect(url_for("products.index"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("products.index"))
