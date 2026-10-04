from flask import Blueprint, jsonify, request
from app.models.product import Product
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import role_required

from app.extensions import db
products_bp = Blueprint("products", __name__)


@products_bp.get("/")
def list_products():
  products = Product.query.all()
  return jsonify([p.to_dict() for p in products]), 200

@products_bp.post("/")
@jwt_required()
@role_required("seller", "admin")
def create_product():
  data = request.get_json()
  name = data.get("name")
  price_cents = data.get("price_cents")
  stock_quantity = data.get("stock_quantity", 0)

  if not name or price_cents is None:
    return jsonify({"error": "name and price_cents are required"}), 400

  seller_id = int(get_jwt_identity())

  product = Product(
    name=name,
    price_cents=price_cents,
    stock_quantity=stock_quantity,
    seller_id=seller_id
  )

  db.session.add(product)
  db.session.commit()

  return jsonify(product.to_dict()), 201
