# models.py

from datetime import datetime
from extensions import db
from flask_login import UserMixin
import os

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    trust_score = db.Column(db.Integer, default=100)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}')"


class Gadget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    price_per_day = db.Column(db.Float)
    stock = db.Column(db.Integer)
    # stores: relative path under /static, e.g. 'uploads/file.jpg' or 'default_gadget.png'
    image = db.Column(db.String(200), default="default_gadget.png")
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    rental_count = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Gadget('{self.name}', '{self.category}', '{self.price_per_day}')"




class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    gadget_id = db.Column(db.Integer, db.ForeignKey('gadget.id'))
    quantity = db.Column(db.Integer, default=1)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    gadget = db.relationship('Gadget', backref=db.backref('cart_items', lazy=True))

    def __repr__(self):
        return f"CartItem(User: {self.user_id}, Gadget: {self.gadget_id}, Quantity: {self.quantity})"


class RentalOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    gadget_id = db.Column(db.Integer, db.ForeignKey('gadget.id'))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    total_days = db.Column(db.Integer)
    total_price = db.Column(db.Float)
    security_deposit = db.Column(db.Float)
    deposit_returned = db.Column(db.Boolean, default=False)
    promo_code = db.Column(db.String(20))
    discount_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20))         # booked, approved, active, returned, cancelled
    payment_status = db.Column(db.String(20)) # pending, paid, failed
    transaction_id = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    gadget = db.relationship('Gadget', backref=db.backref('orders', lazy=True))

    def __repr__(self):
        return f"RentalOrder(User: {self.user_id}, Gadget: {self.gadget_id}, Total: {self.total_price})"


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('rental_order.id'))
    gadget_id = db.Column(db.Integer, db.ForeignKey('gadget.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rating = db.Column(db.Integer)  # 1–5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('RentalOrder', backref=db.backref('reviews', lazy=True))
    gadget = db.relationship('Gadget', backref=db.backref('reviews', lazy=True))
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))

    def __repr__(self):
        return f"Review(Gadget: {self.gadget_id}, User: {self.user_id}, Rating: {self.rating})"


class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    gadget_id = db.Column(db.Integer, db.ForeignKey('gadget.id'))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('wishlist_items', lazy=True))
    gadget = db.relationship('Gadget', backref=db.backref('wishlist_items', lazy=True))

    def __repr__(self):
        return f"Wishlist(User: {self.user_id}, Gadget: {self.gadget_id})"


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f"Notification(User: {self.user_id}, Message: {self.message[:20]}...)"


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject = db.Column(db.String(100))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('feedback', lazy=True))

    def __repr__(self):
        return f"Feedback(User: {self.user_id}, Subject: {self.subject})"


class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # e.g. WELCOME10
    description = db.Column(db.String(200))
    discount_percent = db.Column(db.Float, nullable=False)  # e.g. 10 for 10%
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    max_uses = db.Column(db.Integer, nullable=True)
    times_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Coupon(code={self.code}, discount={self.discount_percent}%)"
