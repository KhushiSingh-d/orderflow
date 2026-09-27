import enum 

from datetime import datetime

from app.extensions import db

class OrderStatus(str,enum.Enum):
  PENDING = "pending"  
  CONFIRMED = "confirmed"
  SHIPPED = "shipped"
  DELIVERED  = "delivered"
  CANCELLED ="cancelled"

class Order(db.Model):
  __tablename__ = "orders"
  id = db.Column(db.Integer, primary_key = True)
  customer_id = db.Column(db.Integer,db.ForeignKey("users.id") , nullable = False)
 
  status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
  total_cents = db.Column(db.Integer , nullable = False)
  created_at = db.Column(db.DateTime , default = datetime.utcnow)
  items = db.relationship("OrderItem", backref="order", lazy="joined", cascade="all, delete-orphan")


class OrderItem(db.Model):
  __tablename__ = "order_items"

  id = db.Column(db.Integer, primary_key=True)
  order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
  quantity = db.Column(db.Integer, nullable=False)
  unit_price_cents = db.Column(db.Integer, nullable=False)
