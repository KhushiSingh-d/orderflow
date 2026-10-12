from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.extensions import db
from app.models.order import Order, OrderItem, OrderStatus, VALID_TRANSITIONS
from app.models.product import Product
from app.utils.decorators import role_required


orders_bp = Blueprint("orders", __name__)


@orders_bp.post("/")
@jwt_required()
@role_required("customer")

def create_order():
  data = request.get_json()
  items = data.get("items")

  if not items:
    return jsonify({"error": "items are required"}), 400

  customer_id = int(get_jwt_identity())

  order = Order(customer_id=customer_id, total_cents=0)
  total_cents = 0

  for item in items:
    product_id = item.get("product_id")
    quantity = item.get("quantity")

    if not isinstance(quantity, int) or quantity <= 0:
      db.session.rollback()
      return jsonify({"error": "quantity must be a positive whole number"}), 400

    product = Product.query.filter_by(id=product_id).with_for_update().first()

    if not product:
      db.session.rollback()
      return jsonify({"error": f"product {product_id} not found"}), 404

    if product.stock_quantity < quantity:
      db.session.rollback()
      return jsonify({"error": f"insufficient stock for {product.name}"}), 400

    product.stock_quantity -= quantity

    order_item = OrderItem(
      product_id=product.id,
      quantity=quantity,
      unit_price_cents=product.price_cents,
    )
    order.items.append(order_item)

    total_cents += product.price_cents * quantity

  order.total_cents = total_cents

  db.session.add(order)
  db.session.commit()

  return jsonify(order.to_dict()), 201


@orders_bp.patch("/<int:order_id>/status")
@jwt_required()
def update_order_status(order_id):
  order = Order.query.get_or_404(order_id)
  data = request.get_json()

  try:
    new_status = OrderStatus(data.get("status"))

  except ValueError:
    return jsonify({"error": "invalid status"}), 400

  role = get_jwt().get("role")
  user_id = int(get_jwt_identity())

  if role == "customer":
    if order.customer_id != user_id:
      return jsonify({"error": "not your order"}), 403

    if new_status != OrderStatus.CANCELLED:
      return jsonify({"error": "customers can only cancel orders"}), 403

  elif role != "admin":
    return jsonify({"error": "insufficient permission"}), 403

  if new_status not in VALID_TRANSITIONS[order.status]:
    return jsonify({"error": f"cannot transition from {order.status.value} to {new_status.value}"}), 400

  order.status = new_status
  db.session.commit()

  return jsonify({"message": "order status updated", "status": order.status.value}), 200