import enum

from datetime import datetime

from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"

class User(db.Model):
  __tablename__ = "users"

  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(255), unique=True, nullable=False)
  password_hash = db.Column(db.String(255), nullable=False)

  role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
  created_at = db.Column(db.DateTime, default=datetime.utcnow)

  def set_password(self, raw_password):
    self.password_hash = generate_password_hash(raw_password)

  def check_password(self, raw_password):
    return check_password_hash(self.password_hash, raw_password)