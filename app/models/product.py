from app.extensions import db

class Product(db.Model):
  __tablename__ = "products"

  id = db.Column(db.Integer, primary_key = True)
  seller_id = db.Column(db.Integer, db.ForeignKey("users.id") , nullable =False)
  name = db.Column(db.String(255), nullable = False)
  price_cents = db.Column(db.Integer , nullable = False)
  stock_quantity = db.Column(db.Integer, nullable=False, default=0)

  __table_args__ = (
      db.CheckConstraint("stock_quantity >= 0", name="ck_stock_non_negative"),
    )

  def to_dict(self):
    return{
      "id": self.id,
      "name": self.name,
      "price_cents": self.price_cents,
      "stock_quantity": self.stock_quantity,
      "seller_id": self.seller_id,
      }