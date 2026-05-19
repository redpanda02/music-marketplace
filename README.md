# MusicMarket — E-Commerce Mini Marketplace
**CS 2712 Software Design & Architecture · Musical Instruments Platform**

---

## Quick Start (3 steps)

### 1. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python run.py
```

Open your browser at **http://127.0.0.1:5000**

The database is created automatically on first run (`instance/marketplace.db`).

---

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@marketplace.com | admin123 |

To test the full flow, register a **Customer** and a **Seller** account from the UI.
The seller account must be approved by the admin before products can be listed.

---

## Project Structure

```
marketplace/
├── run.py                        # Entry point
├── requirements.txt
├── instance/
│   └── marketplace.db            # SQLite database (auto-created)
└── app/
    ├── __init__.py               # App factory + seeding
    ├── models/
    │   ├── user.py               # User, Seller
    │   ├── product.py            # Product, Category
    │   ├── cart.py               # Cart, CartItem
    │   └── order.py              # Order, OrderItem
    ├── blueprints/
    │   ├── auth.py               # Register, Login, Logout
    │   ├── products.py           # Browse, Search, Detail
    │   ├── cart.py               # Cart management
    │   ├── orders.py             # Checkout, History
    │   ├── seller.py             # Seller dashboard + CRUD
    │   └── admin.py              # Admin panel
    ├── templates/
    │   ├── base.html
    │   ├── auth/                 # login.html, register.html
    │   ├── products/             # index.html, detail.html
    │   ├── cart/                 # view.html
    │   ├── orders/               # detail.html, history.html
    │   ├── seller/               # dashboard.html, add/edit product
    │   └── admin/                # dashboard, sellers, categories, users, products
    └── static/
        └── css/style.css
```

---

## Architecture

**Layered + MVC** (Flask Blueprints):

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| Presentation | Jinja2 Templates | Render HTML, no logic |
| Application | Flask Blueprints | Handle requests, validate inputs |
| Domain | SQLAlchemy Models | Business rules (BR-1 to BR-6) |
| Infrastructure | SQLite via SQLAlchemy | Persistence |

---

## Business Rules Implemented

| Rule | Where enforced |
|------|---------------|
| BR-1: Order rejected if stock insufficient | `Order.place_order()` + `Cart.add_item()` |
| BR-2: Only approved sellers can publish | `@approved_seller_required` decorator |
| BR-3: Stock cannot go negative | `Product.update_stock()` |
| BR-4: Order history never deleted | No DELETE on orders, only status updates |
| BR-5: Cart must have ≥ 1 product | `Order.place_order()` |
| BR-6: Only admin manages users/products | `@admin_required` decorator |

---

## User Flows

### Customer
1. Browse products at `/`
2. Register at `/auth/register` (role: Customer)
3. Add products to cart from product detail page
4. Checkout at `/cart/` → Place Order
5. View order history at `/orders/history`

### Seller
1. Register at `/auth/register` (role: Seller)
2. Admin approves account at `/admin/sellers`
3. Add products at `/seller/products/add`
4. Manage products from `/seller/dashboard`

### Admin
1. Login with `admin@marketplace.com` / `admin123`
2. Dashboard at `/admin/dashboard`
3. Approve sellers, manage categories, oversee users and products
