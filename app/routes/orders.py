from flask import Blueprint, jsonify, request
from app.models.order import Order, OrderStatus, VALID_TRANSITIONS
from flask_jwt_extended import jwt_required

from app.extensions import db

orders_bp = Blueprint("orders", __name__)

@orders_bp.patch("/<int:order_id>/status")
@jwt_required()

def update_order_status(order_id):
  order = Order.query.get_or_404(order_id)
  data = request.get_json()
  new_status_str = data.get("status")
  new_status = OrderStatus(new_status_str)
 
  if new_status not in VALID_TRANSITIONS[order.status]:
    return jsonify({"error":f"cannot transition from {order.status.value} to {new_status.value}"}), 400

  order.status = new_status
  db.session.commit()

  return jsonify({"message": "order status updated", "status": order.status.value}), 200


 