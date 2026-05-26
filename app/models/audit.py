from app import db
from datetime import datetime


class AuditLog(db.Model):
    """
    Audit trail for tracking changes to critical marketplace operations.
    Records seller approvals, product changes, stock updates, and order status changes.
    Implements: Technical Recommendation #1 - Add clearer audit-log mechanism
    """
    __tablename__ = "audit_log"

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.Text, nullable=False,
                          default=lambda: datetime.utcnow().isoformat())
    action_type = db.Column(db.Text, nullable=False)  # seller_approval, product_change, stock_update, order_status_change
    entity_type = db.Column(db.Text, nullable=False)  # seller, product, order
    entity_id = db.Column(db.Integer, nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.user_id"))  # who made the change (admin, system)
    old_value = db.Column(db.Text)  # JSON representation of previous state
    new_value = db.Column(db.Text)  # JSON representation of new state
    description = db.Column(db.Text)  # human-readable description

    actor = db.relationship("User")

    @staticmethod
    def log_seller_approval(seller_id, approved, admin_id):
        """Log seller approval status change."""
        log = AuditLog(
            action_type="seller_approval",
            entity_type="seller",
            entity_id=seller_id,
            actor_id=admin_id,
            old_value="0",
            new_value="1" if approved else "0",
            description=f"Seller {seller_id} {'approved' if approved else 'rejected'} by admin {admin_id}"
        )
        db.session.add(log)

    @staticmethod
    def log_product_change(product_id, field_name, old_val, new_val, seller_id):
        """Log product modification."""
        log = AuditLog(
            action_type="product_change",
            entity_type="product",
            entity_id=product_id,
            actor_id=seller_id,
            old_value=str(old_val),
            new_value=str(new_val),
            description=f"Product {product_id} field '{field_name}' changed from {old_val} to {new_val}"
        )
        db.session.add(log)

    @staticmethod
    def log_stock_update(product_id, quantity_change, reason=""):
        """Log stock quantity changes."""
        log = AuditLog(
            action_type="stock_update",
            entity_type="product",
            entity_id=product_id,
            old_value=str(-quantity_change),
            new_value="0",
            description=f"Stock updated by {quantity_change} units. Reason: {reason}"
        )
        db.session.add(log)

    @staticmethod
    def log_order_status_change(order_id, old_status, new_status, admin_id=None):
        """Log order status transitions."""
        log = AuditLog(
            action_type="order_status_change",
            entity_type="order",
            entity_id=order_id,
            actor_id=admin_id,
            old_value=old_status,
            new_value=new_status,
            description=f"Order {order_id} status changed from '{old_status}' to '{new_status}'"
        )
        db.session.add(log)

    def __repr__(self):
        return f"<AuditLog {self.log_id} [{self.action_type}]>"
