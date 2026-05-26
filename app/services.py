"""
Service layer to decouple controllers from ORM-specific queries.
Implements: Technical Recommendation #3 - Strengthen repository/service layer
"""
from app import db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import Seller
from app.models.audit import AuditLog
from sqlalchemy.exc import IntegrityError


class OrderService:
    """Service for order operations with atomic transaction handling."""
    
    @staticmethod
    def place_order_atomic(cart, customer_id):
        """
        Place an order with atomic transaction handling.
        Implements: Technical Recommendation #2 - Clarify transaction handling
        
        Atomicity ensures that stock validation, order creation, order-item creation,
        and stock deduction are either all completed or all rolled back.
        
        Returns (order, error_message, success)
        """
        try:
            # Begin transaction explicitly
            db.session.begin_nested()
            
            # BR-5: cart must not be empty
            if cart.is_empty():
                db.session.rollback()
                return None, "Your cart is empty (BR-5).", False

            # BR-1: validate stock for all items before doing anything
            for cart_item in cart.items:
                product = cart_item.product
                if not product.is_available():
                    db.session.rollback()
                    return None, f"'{product.name}' is no longer available.", False
                if cart_item.quantity > product.stock_quantity:
                    db.session.rollback()
                    return None, (
                        f"Insufficient stock for '{product.name}'. "
                        f"Available: {product.stock_quantity}, "
                        f"Requested: {cart_item.quantity} (BR-1)."
                    ), False

            # All validations passed — create order atomically
            order = Order(customer_id=customer_id)
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
                
                # Log stock update to audit trail
                AuditLog.log_stock_update(product.product_id, cart_item.quantity, 
                                         reason=f"Order {order.order_id} placed")
                
                total += order_item.get_subtotal()

            order.total_amount = total
            order.status = "confirmed"
            
            # Log order status change
            AuditLog.log_order_status_change(order.order_id, "pending", "confirmed")

            # BR-4: order is recorded permanently — cart is cleared, not order
            cart.clear()
            
            # Commit the transaction
            db.session.commit()
            return order, None, True
            
        except IntegrityError as e:
            db.session.rollback()
            return None, f"Database error: {str(e)}", False
        except Exception as e:
            db.session.rollback()
            return None, f"Unexpected error: {str(e)}", False

    @staticmethod
    def get_user_orders(user_id):
        """Retrieve all orders for a user."""
        return Order.query.filter_by(customer_id=user_id).order_by(Order.order_id.desc()).all()
    
    @staticmethod
    def get_order_by_id(order_id):
        """Retrieve a single order by ID."""
        return Order.query.get(order_id)
    
    @staticmethod
    def cancel_order(order_id):
        """Cancel an order if still cancellable."""
        order = Order.query.get(order_id)
        if not order:
            return False, "Order not found"
        
        if order.status not in ("pending", "confirmed"):
            return False, "This order cannot be cancelled"
        
        old_status = order.status
        order.status = "cancelled"
        AuditLog.log_order_status_change(order_id, old_status, "cancelled")
        db.session.commit()
        return True, "Order cancelled successfully"


class ProductService:
    """Service for product operations and inventory management."""
    
    @staticmethod
    def get_active_products():
        """Get all active products."""
        return Product.query.filter_by(is_active=1).all()
    
    @staticmethod
    def get_products_by_category(category_id):
        """Get all active products in a category."""
        return Product.query.filter_by(category_id=category_id, is_active=1).all()
    
    @staticmethod
    def search_products(search_term):
        """Search products by name or description."""
        return Product.query.filter_by(is_active=1).filter(
            Product.name.ilike(f"%{search_term}%")
        ).all()
    
    @staticmethod
    def get_seller_products(seller_id):
        """Get all products from a seller."""
        return Product.query.filter_by(seller_id=seller_id).all()
    
    @staticmethod
    def create_product(name, description, price, stock_quantity, seller_id, 
                      category_id, brand=None, model=None, condition="new", 
                      is_new=1, image_url=None):
        """Create a new product with music-domain fields."""
        product = Product(
            name=name,
            description=description,
            price=price,
            stock_quantity=stock_quantity,
            seller_id=seller_id,
            category_id=category_id,
            brand=brand,
            model=model,
            condition=condition,
            is_new=is_new,
            image_url=image_url,
            is_active=1
        )
        db.session.add(product)
        db.session.commit()
        
        AuditLog.log_product_change(product.product_id, "created", None, 
                                   name, seller_id)
        return product
    
    @staticmethod
    def update_product(product_id, seller_id, **kwargs):
        """Update product fields. Log all changes."""
        product = Product.query.get(product_id)
        if not product or product.seller_id != seller_id:
            return False, "Product not found or unauthorized"
        
        for key, value in kwargs.items():
            if hasattr(product, key):
                old_value = getattr(product, key)
                setattr(product, key, value)
                AuditLog.log_product_change(product_id, key, old_value, value, seller_id)
        
        db.session.commit()
        return True, "Product updated"


class SellerService:
    """Service for seller operations."""
    
    @staticmethod
    def approve_seller(seller_id, admin_id):
        """Approve a seller. Logs action."""
        seller = Seller.query.get(seller_id)
        if not seller:
            return False, "Seller not found"
        
        seller.approve()
        AuditLog.log_seller_approval(seller_id, True, admin_id)
        db.session.commit()
        return True, "Seller approved"
    
    @staticmethod
    def reject_seller(seller_id, admin_id):
        """Reject a seller. Logs action."""
        seller = Seller.query.get(seller_id)
        if not seller:
            return False, "Seller not found"
        
        seller.reject()
        AuditLog.log_seller_approval(seller_id, False, admin_id)
        db.session.commit()
        return True, "Seller rejected"
    
    @staticmethod
    def get_pending_sellers():
        """Get all sellers pending approval."""
        return Seller.query.filter_by(is_approved=0).all()
    
    @staticmethod
    def get_approved_sellers():
        """Get all approved sellers."""
        return Seller.query.filter_by(is_approved=1).all()
    
    @staticmethod
    def update_seller_reputation(seller_id, num_sales=0, rating_delta=0.0):
        """Update seller reputation metrics."""
        seller = Seller.query.get(seller_id)
        if seller:
            seller.total_sales += num_sales
            if seller.num_reviews > 0:
                seller.total_rating = (seller.total_rating * seller.num_reviews + rating_delta) / (seller.num_reviews + 1)
            else:
                seller.total_rating = rating_delta
            seller.num_reviews += 1
            db.session.commit()


class AuditService:
    """Service for audit log operations."""
    
    @staticmethod
    def get_audit_logs(entity_type=None, action_type=None, limit=100):
        """Retrieve audit logs with optional filtering."""
        query = AuditLog.query
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        if action_type:
            query = query.filter_by(action_type=action_type)
        return query.order_by(AuditLog.log_id.desc()).limit(limit).all()
    
    @staticmethod
    def get_entity_history(entity_type, entity_id):
        """Get full history of changes for an entity."""
        return AuditLog.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by(AuditLog.log_id).all()
