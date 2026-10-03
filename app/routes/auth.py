from flask import Blueprint
from flask import request, jsonify
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.user import User
auth_bp = Blueprint("auth", __name__)

@auth_bp.get("/ping")
def ping():
  return{"message": "auth blueprint is alive"}, 200

@auth_bp.post("/register")
def register():
  data = request.get_json()
  email = data.get("email")
  password = data.get("password")

  if not email or not password:
    return jsonify({"error": "email and password are required"}), 400

  if User.query.filter_by(email=email).first():
    return jsonify({"error": " email already registered"}), 409

  user = User(email=email)
  user.set_password(password)

  db.session.add(user)
  db.session.commit()

  return jsonify({"message": "user registered", "email": user.email}), 201

@auth_bp.post("/login")
def login():
  data = request.get_json()
  email = data.get("email")
  password = data.get("password")

  user = User.query.filter_by(email=email).first()

  if not user or not user.check_password(password or ""):
    return jsonify({"error": "invalid credentials"}), 401

  access_token = create_access_token(identity=str(user.id))

  return jsonify({"access_token": access_token}), 200

