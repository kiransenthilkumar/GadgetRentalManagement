from flask import Flask, render_template, request, redirect, url_for, flash, make_response, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps # Import wraps
from email_service import send_welcome_email, send_order_confirmation_email, send_payment_receipt_email, send_deposit_refund_confirmation_email # Import email functions
import csv # Import csv
import io # Import io
import os # Import os
from werkzeug.utils import secure_filename # Import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gadget.db'
app.config['SECRET_KEY'] = 'your_secret_key' # Replace with a strong secret key

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize extensions
from extensions import db, login_manager
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models after db and login_manager are initialized
from models import User, Gadget, CartItem, RentalOrder, Review, Wishlist, Notification, Feedback # Import Feedback model

# Admin Required Decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route('/')
def home():
    featured = Gadget.query.filter_by(is_active=True, is_featured=True) \
                           .order_by(Gadget.created_at.desc()).limit(6).all()
    if not featured:
        featured = Gadget.query.filter_by(is_active=True) \
                               .order_by(Gadget.rental_count.desc()).limit(6).all()
    categories = [c[0] for c in db.session.query(Gadget.category).distinct()]
    return render_template('home.html', featured=featured, categories=categories)


@app.route('/gadgets')
def gadgets():
    category = request.args.get('category')
    search_query = request.args.get('search')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort_by', 'popularity')

    gadgets_query = Gadget.query.filter_by(is_active=True)

    if category:
        gadgets_query = gadgets_query.filter_by(category=category)
    if search_query:
        gadgets_query = gadgets_query.filter(Gadget.name.ilike(f'%{search_query}%'))
    if min_price:
        gadgets_query = gadgets_query.filter(Gadget.price_per_day >= min_price)
    if max_price:
        gadgets_query = gadgets_query.filter(Gadget.price_per_day <= max_price)

    if sort_by == 'price_low_high':
        gadgets_query = gadgets_query.order_by(Gadget.price_per_day.asc())
    elif sort_by == 'popularity':
        gadgets_query = gadgets_query.order_by(Gadget.rental_count.desc())
    elif sort_by == 'newest':
        gadgets_query = gadgets_query.order_by(Gadget.created_at.desc())
    
    gadgets = gadgets_query.all()
    categories = [g.category for g in Gadget.query.with_entities(Gadget.category).distinct()]

    return render_template('gadgets.html', gadgets=gadgets, categories=categories,
                           selected_category=category, search_query=search_query,
                           min_price=min_price, max_price=max_price, sort_by=sort_by)

@app.route('/gadget/<int:gadget_id>')
def gadget_detail(gadget_id):
    gadget = Gadget.query.get_or_404(gadget_id)
    gadget.view_count += 1
    reviews = Review.query.filter_by(gadget_id=gadget.id).order_by(Review.created_at.desc()).all()
    db.session.commit()
    return render_template('gadget_detail.html', gadget=gadget, reviews=reviews)

@app.route('/add-to-cart/<int:gadget_id>', methods=['POST'])
@login_required
def add_to_cart(gadget_id):
    gadget = Gadget.query.get_or_404(gadget_id)
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    if not start_date_str or not end_date_str:
        flash('Please select both start and end dates.', 'danger')
        return redirect(url_for('gadget_detail', gadget_id=gadget.id))

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    if start_date < datetime.utcnow().date():
        flash('Start date cannot be in the past.', 'danger')
        return redirect(url_for('gadget_detail', gadget_id=gadget.id))

    if end_date < start_date:
        flash('End date cannot be before start date.', 'danger')
        return redirect(url_for('gadget_detail', gadget_id=gadget.id))

    # Check for minimum 1-day rental
    if (end_date - start_date).days < 0:
        flash('Minimum rental period is 1 day.', 'danger')
        return redirect(url_for('gadget_detail', gadget_id=gadget.id))

    # Check for maximum 30-day rental
    if (end_date - start_date).days > 29:
        flash('Maximum rental period is 30 days.', 'danger')
        return redirect(url_for('gadget_detail', gadget_id=gadget.id))

    # Basic stock availability check (will be enhanced during order placement)
    existing_cart_item = CartItem.query.filter_by(user_id=current_user.id, gadget_id=gadget.id, 
                                                 start_date=start_date, end_date=end_date).first()

    if existing_cart_item:
        existing_cart_item.quantity += 1
        flash('Gadget quantity updated in cart.', 'info')
    else:
        new_cart_item = CartItem(user_id=current_user.id, gadget_id=gadget.id,
                                 start_date=start_date, end_date=end_date, quantity=1)
        db.session.add(new_cart_item)
        flash('Gadget added to cart!', 'success')
    
    db.session.commit()
    return redirect(url_for('cart'))

PROMO_CODES = {
    'WELCOME10': 0.10, # 10% discount
    'SUMMER20': 0.20 # 20% discount
}

@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_cart_price = 0
    promo_code_applied = None
    discount_amount = 0

    for item in cart_items:
        total_days = (item.end_date - item.start_date).days + 1
        item.subtotal = item.gadget.price_per_day * item.quantity * total_days
        total_cart_price += item.subtotal
    
    if request.method == 'POST':
        promo_code = request.form.get('promo_code', '').upper()
        if promo_code in PROMO_CODES:
            discount_percentage = PROMO_CODES[promo_code]
            discount_amount = total_cart_price * discount_percentage
            total_cart_price -= discount_amount
            promo_code_applied = promo_code
            flash(f'Promo code {promo_code} applied! You saved ₹{discount_amount:.2f}.', 'success')
        else:
            flash('Invalid promo code.', 'danger')

    return render_template('cart.html', cart_items=cart_items, total_cart_price=total_cart_price,
                           promo_code_applied=promo_code_applied, discount_amount=discount_amount)

@app.route('/update-cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('You are not authorized to update this cart item.', 'danger')
        return redirect(url_for('cart'))

    quantity = request.form.get('quantity', type=int)
    if quantity is not None and quantity > 0:
        cart_item.quantity = quantity
        db.session.commit()
        flash('Cart updated successfully.', 'success')
    else:
        flash('Invalid quantity.', 'danger')
    return redirect(url_for('cart'))

@app.route('/remove-from-cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('You are not authorized to remove this cart item.', 'danger')
        return redirect(url_for('cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

@app.route('/clear-cart')
@login_required
def clear_cart():
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Your cart has been cleared.', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty. Please add items before checking out.', 'danger')
        return redirect(url_for('gadgets'))

    total_rental_price = 0
    total_deposit = 0 
    promo_code_applied = request.form.get('promo_code_applied') # Get promo code from hidden input
    discount_amount = request.form.get('discount_amount', type=float) or 0.0 # Get discount from hidden input

    for item in cart_items:
        total_days = (item.end_date - item.start_date).days + 1
        item.subtotal = item.gadget.price_per_day * item.quantity * total_days
        total_rental_price += item.subtotal

    # Always initialize deposit
        item_deposit = 0

    # High-value item deposit
        if item.gadget.price_per_day * total_days > 1000:
            item_deposit = item.subtotal * 0.5
            total_deposit += item_deposit

        item.security_deposit = item_deposit

    final_total_payable = total_rental_price + total_deposit - discount_amount # Apply discount

    if request.method == 'POST':
        address = request.form.get('address')
        if not address:
            flash('Please provide a delivery address.', 'danger')
            return render_template('checkout.html', cart_items=cart_items, total_rental_price=total_rental_price, 
                                   total_deposit=total_deposit, final_total_payable=final_total_payable, 
                                   promo_code_applied=promo_code_applied, discount_amount=discount_amount, user=current_user)
        
        current_user.address = address
        db.session.commit()

        # --- Stock Availability Check before placing order ---
        for item in cart_items:
            if item.gadget.stock < item.quantity:
                flash(f'Not enough stock for {item.gadget.name}. Available: {item.gadget.stock}', 'danger')
                return redirect(url_for('cart'))

        # --- Create Orders ---
        for item in cart_items:
            total_days = (item.end_date - item.start_date).days + 1
            total_price_item = item.gadget.price_per_day * item.quantity * total_days
            item_deposit_amount = 0
            if item.gadget.price_per_day * total_days > 1000: # Recalculate deposit for order creation
                item_deposit_amount = total_price_item * 0.5

            new_order = RentalOrder(
                user_id=current_user.id,
                gadget_id=item.gadget.id,
                start_date=item.start_date,
                end_date=item.end_date,
                total_days=total_days,
                total_price=total_price_item,
                security_deposit=item_deposit_amount, 
                promo_code=promo_code_applied, # Save promo code
                discount_amount=discount_amount, # Save discount amount
                status='booked',
                payment_status='pending'
            )
            db.session.add(new_order)
            item.gadget.stock -= item.quantity # Reduce stock
            item.gadget.rental_count += item.quantity # Increase rental count
        
        CartItem.query.filter_by(user_id=current_user.id).delete() # Clear cart after placing order
        db.session.commit()
        flash('Your order has been placed successfully!', 'success')
        
        # Send order confirmation email for each order placed
        for item in cart_items:
            order_for_email = RentalOrder.query.filter_by(user_id=current_user.id, gadget_id=item.gadget.id,
                                                           start_date=item.start_date, end_date=item.end_date).first()
            if order_for_email:
                send_order_confirmation_email(current_user.email, current_user.name, order_for_email.id,
                                              item.gadget.name, order_for_email.total_price,
                                              order_for_email.start_date, order_for_email.end_date)

        return redirect(url_for('payment')) # Redirect to payment page

    return render_template('checkout.html', cart_items=cart_items, total_rental_price=total_rental_price,
                           total_deposit=total_deposit, final_total_payable=final_total_payable,
                           promo_code_applied=promo_code_applied, discount_amount=discount_amount, user=current_user)

@app.route('/order-confirmation')
@login_required
def order_confirmation():
    order_id = request.args.get('order_id', type=int)
    transaction_id = request.args.get('transaction_id')
    order = RentalOrder.query.get_or_404(order_id) if order_id else None
    return render_template('order_confirmation.html', order=order, transaction_id=transaction_id)

@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    # Get the latest pending order for the current user
    pending_order = RentalOrder.query.filter_by(
        user_id=current_user.id, 
        payment_status='pending'
    ).order_by(RentalOrder.created_at.desc()).first()

    if not pending_order:
        flash('No pending orders to pay for.', 'danger')
        return redirect(url_for('orders'))

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        card_number = request.form.get('card_number')

        transaction_id = "TXN_" + str(datetime.utcnow().timestamp()).replace('.', '')
        payment_status = 'failed'
        message = 'Payment failed.'

        # -------------------------
        # PAYMENT VALIDATION LOGIC
        # -------------------------
        if payment_method == 'card':
            if card_number == '4242424242424242':
                payment_status = 'paid'
                message = 'Payment completed successfully!'
            elif card_number == '4000000000000000':
                payment_status = 'failed'
                message = 'Payment failed: Insufficient funds.'
            else:
                payment_status = 'failed'
                message = 'Payment failed: Invalid card number.'

        elif payment_method == 'upi':
            payment_status = 'paid'
            message = 'UPI Payment completed successfully!'

        elif payment_method == 'cash_on_pickup':
            payment_status = 'pending'
            message = 'Order confirmed. Payment to be made on pickup.'

        else:
            flash('Invalid payment method selected.', 'danger')
            return redirect(url_for('payment'))

        # -------------------------
        # UPDATE ORDER PAYMENT STATUS
        # -------------------------
        pending_order.payment_status = payment_status
        pending_order.transaction_id = transaction_id
        db.session.commit()

        # -------------------------
        # 🔔 CREATE NOTIFICATIONS
        # -------------------------
        if payment_status == 'paid':
            # Email
            send_payment_receipt_email(
                current_user.email,
                current_user.name,
                pending_order.id,
                transaction_id,
                pending_order.total_price
            )

            # Notification → user sees in /notifications
            notif = Notification(
                user_id=current_user.id,
                message=f"Your payment for order #{pending_order.id} was successful."
            )
            db.session.add(notif)
            db.session.commit()

            flash(message, 'success')
            return redirect(url_for(
                'order_confirmation',
                order_id=pending_order.id,
                transaction_id=transaction_id
            ))

        # -------------------------
        # CASH ON PICKUP → SEND NOTIFICATION
        # -------------------------
        if payment_method == 'cash_on_pickup':
            notif = Notification(
                user_id=current_user.id,
                message=f"Order #{pending_order.id} confirmed. Pay at pickup."
            )
            db.session.add(notif)
            db.session.commit()

            flash(message, 'info')
            return redirect(url_for('orders'))

        # -------------------------
        # PAYMENT FAILED
        # -------------------------
        flash(message, 'danger')
        return redirect(url_for('payment'))

    return render_template('payment.html', order=pending_order)


@app.route('/orders')
@login_required
def orders():
    user_orders = RentalOrder.query.filter_by(user_id=current_user.id).order_by(RentalOrder.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders, today=datetime.utcnow().date())

@app.route('/orders/<int:order_id>')
@login_required
def order_details(order_id):
    order = RentalOrder.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You are not authorized to view this order.', 'danger')
        return redirect(url_for('orders'))
    return render_template('order_details.html', order=order, today=datetime.utcnow().date())

@app.route('/cancel-order/<int:order_id>')
@login_required
def cancel_order(order_id):
    order = RentalOrder.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('You are not authorized to cancel this order.', 'danger')
        return redirect(url_for('orders'))

    # Only cancel if order is still booked and has NOT started
    if order.status == 'booked' and order.start_date > datetime.utcnow().date():

        # Restore stock ONLY IF stock was previously deducted
        if order.payment_status in ['paid', 'pending']:  
            order.gadget.stock += 1

        order.status = 'cancelled'
        db.session.commit()
        flash('Order cancelled successfully.', 'success')
    else:
        flash('Order cannot be cancelled.', 'danger')

    return redirect(url_for('orders'))

@app.route('/submit-review/<int:order_id>', methods=['GET', 'POST'])
@login_required
def submit_review(order_id):
    order = RentalOrder.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('orders'))

    if order.status != "returned":
        flash("You can submit a review only after the order is returned.", "danger")
        return redirect(url_for('orders'))

    existing = Review.query.filter_by(order_id=order.id).first()
    if existing:
        flash("You have already submitted a review for this order.", "info")
        return redirect(url_for('order_details', order_id=order_id))

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        comment = request.form.get("comment")

        if not (1 <= rating <= 5):
            flash("Rating must be between 1 and 5.", "danger")
            return render_template("submit_review.html", order=order)

        review = Review(
            order_id=order.id,
            gadget_id=order.gadget.id,
            user_id=current_user.id,
            rating=rating,
            comment=comment
        )

        db.session.add(review)
        db.session.commit()

        # Recalculate average rating
        reviews = Review.query.filter_by(gadget_id=order.gadget.id).all()
        order.gadget.avg_rating = sum(r.rating for r in reviews) / len(reviews)
        db.session.commit()

        # 🔔 NEW: Add user notification
        notif = Notification(
            user_id=current_user.id,
            message=f"Thank you! Your review for {order.gadget.name} has been submitted."
        )
        db.session.add(notif)
        db.session.commit()

        flash("Review submitted successfully!", "success")
        return redirect(url_for('order_details', order_id=order_id))

    return render_template('submit_review.html', order=order)


@app.route('/reviews')
def reviews():
    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('reviews.html', reviews=all_reviews)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.is_admin and check_password_hash(user.password, password):
            login_user(user, remember=True, force=True)
            session["is_admin_session"] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
    return render_template('admin/admin_login.html')

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():

    total_gadgets = Gadget.query.count()
    active_rentals = RentalOrder.query.filter_by(status="active").count()
    pending_approvals = RentalOrder.query.filter_by(status="booked").count()

    today = datetime.today().date()
    today_revenue = db.session.query(
        db.func.sum(RentalOrder.total_price)
    ).filter(
        db.func.date(RentalOrder.created_at) == today,
        RentalOrder.payment_status == 'paid'
    ).scalar() or 0

    total_revenue = db.session.query(
        db.func.sum(RentalOrder.total_price)
    ).filter(RentalOrder.payment_status == 'paid').scalar() or 0

    # LOW STOCK ITEMS (< 3)
    low_stock_items = Gadget.query.filter(Gadget.stock < 3).all()
    low_stock_alerts = len(low_stock_items)

    return render_template(
        "admin/admin_dashboard.html",
        total_gadgets=total_gadgets,
        active_rentals=active_rentals,
        today_revenue=today_revenue,
        total_revenue=total_revenue,
        pending_approvals=pending_approvals,
        low_stock_alerts=low_stock_alerts,
        low_stock_items=low_stock_items
    )


@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    status_filter = request.args.get('status')
    orders_query = RentalOrder.query.order_by(RentalOrder.created_at.desc())

    if status_filter and status_filter != 'all':
        orders_query = orders_query.filter_by(status=status_filter)
    
    all_orders = orders_query.all()
    return render_template('admin/admin_orders.html', orders=all_orders, selected_status=status_filter)

@app.route('/admin/order/<int:order_id>/approve')
@login_required
@admin_required
def admin_approve_order(order_id):
    order = RentalOrder.query.get_or_404(order_id)

    if order.status == 'booked':
        order.status = 'approved'

        # 🔔 Create notification for user
        notification = Notification(
            user_id=order.user_id,
            message=f"Your order #{order.id} has been approved."
        )
        db.session.add(notification)

        db.session.commit()  # ✅ Single commit for both updates

        flash(f"Order {order.id} approved.", "success")

    else:
        flash(f"Order {order.id} cannot be approved from current status.", "danger")

    return redirect(url_for('admin_orders'))


@app.route('/admin/order/<int:order_id>/reject')
@login_required
@admin_required
def admin_reject_order(order_id):
    order = RentalOrder.query.get_or_404(order_id)

    if order.status == 'booked':
        
        # Return stock because stock was already reduced at checkout
        order.gadget.stock += 1

        order.status = 'cancelled'
        db.session.commit()

        # 🔔 Notify user
        db.session.add(Notification(
            user_id=order.user_id,
            message=f"Your order #{order.id} has been rejected."
        ))
        db.session.commit()

        flash(f'Order {order.id} rejected.', 'info')

    else:
        flash(f'Order {order.id} cannot be rejected from current status.', 'danger')

    return redirect(url_for('admin_orders'))


@app.route('/admin/order/<int:order_id>/mark-active')
@login_required
@admin_required
def admin_mark_active(order_id):
    order = RentalOrder.query.get_or_404(order_id)

    if order.status == 'approved':
        order.status = 'active'

        # 🔔 Notify user
        notification = Notification(
            user_id=order.user_id,
            message=f"Your order #{order.id} is now Active and being processed."
        )
        db.session.add(notification)

        db.session.commit()  # ✅ One commit for everything

        flash(f"Order {order.id} marked as Active.", "success")
    else:
        flash(f"Order {order.id} cannot be marked active from current status.", "danger")

    return redirect(url_for('admin_orders'))


@app.route('/admin/order/<int:order_id>/mark-delivered')
@login_required
@admin_required
def admin_mark_delivered(order_id):
    order = RentalOrder.query.get_or_404(order_id)

    if order.status == 'active':
        order.status = 'delivered'

        # 🔔 Notify user
        notif = Notification(
            user_id=order.user_id,
            message=f"Your order #{order.id} has been delivered."
        )
        db.session.add(notif)

        db.session.commit()
        flash(f'Order {order.id} marked as delivered.', 'success')

    else:
        flash(f'Order {order.id} cannot be marked delivered from current status.', 'danger')

    return redirect(url_for('admin_orders'))


@app.route('/admin/order/<int:order_id>/mark-returned')
@login_required
@admin_required
def admin_mark_returned(order_id):
    order = RentalOrder.query.get_or_404(order_id)

    if order.status in ['delivered', 'active']:
        order.status = 'returned'

        # Return gadget to stock
        order.gadget.stock += 1

        # 🔔 Notify user
        notif = Notification(
            user_id=order.user_id,
            message=f"Your order #{order.id} has been marked Returned. Thank you!"
        )
        db.session.add(notif)

        db.session.commit()
        flash(f'Order {order.id} marked as returned. Gadget stock updated.', 'success')

    else:
        flash(f'Order {order.id} cannot be marked returned from current status.', 'danger')

    return redirect(url_for('admin_orders'))


@app.route('/admin/order/<int:order_id>/refund-deposit')
@login_required
@admin_required
def admin_refund_deposit(order_id):
    order = RentalOrder.query.get_or_404(order_id)

    if order.status == 'returned' and not order.deposit_returned:
        order.deposit_returned = True

        # 🔔 Notify user
        notif = Notification(
            user_id=order.user_id,
            message=f"Your security deposit for order #{order.id} has been refunded."
        )
        db.session.add(notif)

        db.session.commit()

        # Email confirmation
        send_deposit_refund_confirmation_email(
            order.user.email, order.user.name, order.id, order.security_deposit
        )

        flash(f'Deposit for order {order.id} refunded.', 'success')

    else:
        flash(f'Deposit for order {order.id} cannot be refunded.', 'danger')

    return redirect(url_for('admin_orders'))


@app.route('/admin/order/<int:order_id>/cancel')
@login_required
@admin_required
def admin_cancel_order(order_id):
    order = RentalOrder.query.get_or_404(order_id)

    if order.status in ['cancelled', 'returned']:
        flash("Order is already completed or cancelled.", "info")
        return redirect(url_for('admin_orders'))

    # Only return stock if order was active (stock already reduced)
    if order.status in ['approved', 'active', 'delivered']:
        order.gadget.stock += 1

    order.status = 'cancelled'

    # Notify user
    notif = Notification(
        user_id=order.user_id,
        message=f"Your order #{order.id} has been cancelled by the admin."
    )
    db.session.add(notif)

    db.session.commit()
    flash(f"Order {order.id} cancelled successfully.", "success")

    return redirect(url_for('admin_orders'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(name=name, email=email, password=hashed_password, phone=phone)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            send_welcome_email(email, name) # Send welcome email
            return redirect(url_for('login'))
        except:
            flash('That email is already registered. Please use a different email.', 'danger')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session.pop("is_admin_session", None)  # remove admin session
            login_user(user, remember=True)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.email = request.form.get('email')
        current_user.phone = request.form.get('phone')
        current_user.address = request.form.get('address')
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=current_user)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('new_password')

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            db.session.commit()
            flash('Your password has been reset successfully. Please log in with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('No account found with that email address.', 'danger')
    return render_template('forgot_password.html')

@app.route('/add-to-wishlist/<int:gadget_id>')
@login_required
def add_to_wishlist(gadget_id):
    gadget = Gadget.query.get_or_404(gadget_id)
    existing_wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, gadget_id=gadget.id).first()

    if existing_wishlist_item:
        flash('Gadget is already in your wishlist.', 'info')
    else:
        new_wishlist_item = Wishlist(user_id=current_user.id, gadget_id=gadget.id)
        db.session.add(new_wishlist_item)
        db.session.commit()
        flash('Gadget added to your wishlist!', 'success')
    return redirect(url_for('gadget_detail', gadget_id=gadget.id))

@app.route('/remove-from-wishlist/<int:item_id>')
@login_required
def remove_from_wishlist(item_id):
    wishlist_item = Wishlist.query.get_or_404(item_id)
    if wishlist_item.user_id != current_user.id:
        flash('You are not authorized to remove this item from wishlist.', 'danger')
        return redirect(url_for('wishlist'))
    
    db.session.delete(wishlist_item)
    db.session.commit()
    flash('Item removed from wishlist.', 'info')
    return redirect(url_for('wishlist'))

@app.route('/   ')
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', wishlist_items=wishlist_items)

@app.route('/move-to-cart/<int:item_id>')
@login_required
def move_to_cart(item_id):
    wishlist_item = Wishlist.query.get_or_404(item_id)
    if wishlist_item.user_id != current_user.id:
        flash('You are not authorized to move this item to cart.', 'danger')
        return redirect(url_for('wishlist'))
    
    # Check if item is already in cart for the same dates (dummy dates for now)
    # For simplicity, we'll add it with today's date for 1 day rental
    today = datetime.utcnow().date()
    existing_cart_item = CartItem.query.filter_by(user_id=current_user.id, gadget_id=wishlist_item.gadget.id,
                                                 start_date=today, end_date=today).first()
    
    if existing_cart_item:
        existing_cart_item.quantity += 1
    else:
        new_cart_item = CartItem(user_id=current_user.id, gadget_id=wishlist_item.gadget.id,
                                 start_date=today, end_date=today, quantity=1)
        db.session.add(new_cart_item)
    
    db.session.delete(wishlist_item) # Remove from wishlist after moving to cart
    db.session.commit()
    flash('Item moved to cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    # For simplicity, we'll mark them as read when viewed
    for notif in user_notifications:
        if not notif.is_read:
            notif.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=user_notifications)


@app.route('/mark-notification-read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        flash('You are not authorized to mark this notification.', 'danger')
        return redirect(url_for('notifications'))
    
    notification.is_read = True
    db.session.commit()
    flash('Notification marked as read.', 'info')
    return redirect(url_for('notifications'))

# Example of creating a notification (e.g., for new gadget alert - normally done by admin)
def create_new_gadget_notification(gadget_name):
    all_users = User.query.all()
    for user in all_users:
        new_notif = Notification(user_id=user.id, message=f'New gadget alert! Check out the {gadget_name}!')
        db.session.add(new_notif)
    db.session.commit()
    print(f"Notifications created for new gadget: {gadget_name}")

# Example of creating a cart reminder notification (would be a scheduled task)
def create_cart_reminder_notification(user_id):
    user = User.query.get(user_id)
    if user:
        cart_items = CartItem.query.filter_by(user_id=user_id).count()
        if cart_items > 0:
            # Check if a reminder was sent recently, to avoid spamming
            # For simplicity, just send one for now
            new_notif = Notification(user_id=user_id, message='You have items in your cart! Complete your order soon.')
            db.session.add(new_notif)
            db.session.commit()
            print(f"Cart reminder notification sent to {user.email}")

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')

        # Validate
        if not subject or not message:
            flash("Please fill out all fields.", "danger")
            return redirect(url_for('feedback'))

        # Save feedback
        new_feedback = Feedback(
            user_id=current_user.id,
            subject=subject,
            message=message
        )
        db.session.add(new_feedback)
        db.session.commit()

        flash("Your feedback has been submitted successfully!", "success")

        # 🔔 Notify ALL admins
        admins = User.query.filter_by(is_admin=True).all()
        for admin in admins:
            notif = Notification(
                user_id=admin.id,
                message=f"New feedback from {current_user.name}: {subject}"
            )
            db.session.add(notif)

        db.session.commit()

        return redirect(url_for('feedback'))

    # GET request → show feedback form
    return render_template("feedback.html")



@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    return render_template('admin/admin_reports.html')

@app.route('/admin/reports/daily-revenue')
@login_required
@admin_required
def daily_revenue_report():
    format_type = request.args.get('format')

    # Query raw results
    raw_data = db.session.query(
        db.func.date(RentalOrder.created_at).label("date"),
        db.func.count(RentalOrder.id).label("orders"),
        db.func.sum(RentalOrder.total_price).label("revenue"),
        db.func.avg(RentalOrder.total_price).label("avg_revenue"),
        db.func.max(RentalOrder.total_price).label("max_order"),
        db.func.min(RentalOrder.total_price).label("min_order"),
        db.func.count(db.func.distinct(RentalOrder.user_id)).label("unique_customers"),
        db.func.sum(RentalOrder.total_days).label("total_days"),
        db.func.avg(RentalOrder.total_days).label("avg_days")
    ).filter(RentalOrder.payment_status == 'paid') \
     .group_by(db.func.date(RentalOrder.created_at)) \
     .order_by(db.func.date(RentalOrder.created_at).desc()) \
     .all()

    # Normalize data for template + CSV
    data = []
    for row in raw_data:
        date_value = row.date

        # Convert datetime → string
        if hasattr(date_value, "strftime"):
            date_str = date_value.strftime("%Y-%m-%d")
        else:
            date_str = str(date_value)

        data.append({
            "date": date_str,
            "orders": row.orders,
            "revenue": row.revenue or 0,
            "avg_revenue": row.avg_revenue or 0,
            "max_order": row.max_order or 0,
            "min_order": row.min_order or 0,
            "unique_customers": row.unique_customers,
            "total_days": row.total_days or 0,
            "avg_days": row.avg_days or 0
        })

    # ----- CSV EXPORT -----
    if format_type == "csv":
        si = io.StringIO()
        writer = csv.writer(si)

        writer.writerow([
            "Date", "Total Orders", "Revenue (₹)", "Avg Revenue (₹)",
            "Max Order (₹)", "Min Order (₹)",
            "Unique Customers", "Total Rental Days", "Avg Rental Days"
        ])

        for row in data:
            writer.writerow([
                row["date"],
                row["orders"],
                f"{row['revenue']:.2f}",
                f"{row['avg_revenue']:.2f}",
                f"{row['max_order']:.2f}",
                f"{row['min_order']:.2f}",
                row["unique_customers"],
                row["total_days"],
                f"{row['avg_days']:.2f}"
            ])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=daily_revenue_report.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    # Render HTML
    return render_template("admin/reports/daily_revenue_report.html", data=data)


@app.route("/admin/reports/most-rented-gadgets")
@login_required
@admin_required
def most_rented_gadgets_report():
    format_type = request.args.get("format")

    data = db.session.query(
        Gadget.name.label("gadget"),
        Gadget.category.label("category"),
        db.func.count(RentalOrder.id).label("total_rentals"),
        db.func.sum(RentalOrder.total_days).label("total_days"),
        db.func.count(db.func.distinct(RentalOrder.user_id)).label("unique_users"),
        db.func.sum(RentalOrder.total_price).label("total_revenue"),
        db.func.avg(RentalOrder.total_price).label("avg_revenue"),
        db.func.avg(RentalOrder.total_days).label("avg_days"),
        db.func.max(RentalOrder.created_at).label("last_rented")
    ).join(RentalOrder) \
     .filter(RentalOrder.payment_status == "paid") \
     .group_by(Gadget.id) \
     .order_by(db.desc("total_rentals")) \
     .all()

    if format_type == "csv":
        si = io.StringIO()
        writer = csv.writer(si)

        writer.writerow([
            "Gadget", "Category", "Total Rentals", "Total Days",
            "Unique Users", "Total Revenue (₹)", "Avg Revenue (₹)",
            "Avg Days", "Last Rented"
        ])

        for row in data:
            last_rented = row.last_rented.strftime("%Y-%m-%d") if row.last_rented else ""

            writer.writerow([
                row.gadget,
                row.category,
                row.total_rentals,
                row.total_days,
                row.unique_users,
                f"{row.total_revenue:.2f}",
                f"{row.avg_revenue:.2f}",
                f"{row.avg_days:.2f}",
                last_rented
            ])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=most_rented_gadgets_report.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    return render_template("admin/reports/most_rented_gadgets_report.html", data=data)

@app.route('/admin/reports/user-activity')
@login_required
@admin_required
def user_activity_report():
    format_type = request.args.get("format")

    data = db.session.query(
        User.name,
        User.email,
        User.phone,
        db.func.count(RentalOrder.id).label("orders"),
        db.func.sum(RentalOrder.total_price).label("revenue"),
        db.func.avg(RentalOrder.total_price).label("avg_revenue"),
        db.func.sum(RentalOrder.total_days).label("total_days"),
        db.func.avg(RentalOrder.total_days).label("avg_days"),
        db.func.max(RentalOrder.created_at).label("last_order")
    ).join(RentalOrder) \
     .filter(RentalOrder.payment_status == "paid") \
     .group_by(User.id) \
     .order_by(db.desc("orders")) \
     .all()

    # CSV Export
    if format_type == "csv":
        si = io.StringIO()
        writer = csv.writer(si)

        writer.writerow([
            "User", "Email", "Phone",
            "Total Orders", "Total Revenue (₹)", "Avg Revenue (₹)",
            "Total Rental Days", "Avg Days",
            "Last Order Date"
        ])

        for row in data:
            last_order = row.last_order.strftime("%Y-%m-%d") if row.last_order else ""

            writer.writerow([
                row.name,
                row.email,
                row.phone or "",
                row.orders,
                f"{row.revenue:.2f}" if row.revenue else "0.00",
                f"{row.avg_revenue:.2f}" if row.avg_revenue else "0.00",
                row.total_days or 0,
                f"{row.avg_days:.2f}" if row.avg_days else "0.00",
                last_order
            ])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=user_activity_report.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    return render_template("admin/reports/user_activity_report.html", data=data)



# ------------------------------
# ADMIN — VIEW ALL FEEDBACK
# ------------------------------
@app.route('/admin/feedback')
@login_required
@admin_required
def admin_feedback():
    feedback_items = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template("admin/admin_feedback.html", feedback_items=feedback_items)


# ------------------------------
# ADMIN — MARK FEEDBACK RESOLVED
# ------------------------------
@app.route('/admin/feedback/<int:feedback_id>/resolve')
@login_required
@admin_required
def admin_resolve_feedback(feedback_id):
    item = Feedback.query.get_or_404(feedback_id)

    if item.status == "resolved":
        flash("This feedback is already resolved.", "info")
        return redirect(url_for('admin_feedback'))

    # Mark as resolved
    item.status = "resolved"
    db.session.commit()

    # Notify user
    notif = Notification(
        user_id=item.user_id,
        message=f"Your feedback '{item.subject}' has been marked as resolved by admin."
    )
    db.session.add(notif)
    db.session.commit()

    flash("Feedback marked as resolved.", "success")
    return redirect(url_for('admin_feedback'))


@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    return render_template('admin/admin_users.html', users=users)


@app.route('/admin/user/<int:user_id>/mark-verified')
@login_required
@admin_required
def admin_mark_user_verified(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_verified:
        user.is_verified = True
        db.session.commit()
        flash(f'User {user.name} marked as verified.', 'success')
    else:
        flash(f'User {user.name} is already verified.', 'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/deactivate')
@login_required
@admin_required
def admin_deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_active:
        user.is_active = False # Assuming an 'is_active' flag in User model for deactivation
        db.session.commit()
        flash(f'User {user.name} deactivated.', 'success')
    else:
        flash(f'User {user.name} is already deactivated.', 'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/rental-history')
@login_required
@admin_required
def admin_user_rental_history(user_id):
    user = User.query.get_or_404(user_id)
    user_orders = RentalOrder.query.filter_by(user_id=user.id).order_by(RentalOrder.created_at.desc()).all()
    return render_template('admin/admin_user_rental_history.html', user=user, orders=user_orders)

@app.route('/admin/gadgets')
@login_required
@admin_required
def admin_gadgets():
    all_gadgets = Gadget.query.order_by(Gadget.created_at.desc()).all()
    return render_template('admin/admin_gadgets.html', gadgets=all_gadgets)

@app.before_request
def ensure_images_valid():
    for g in Gadget.query.all():
        img_path = os.path.join(app.root_path, "static", g.image)
        if not os.path.exists(img_path):
            g.image = "default_gadget.png"
    db.session.commit()

@app.route('/admin/gadgets/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_gadget():
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        description = request.form.get('description')
        price_per_day = request.form.get('price_per_day', type=float)
        stock = request.form.get('stock', type=int)
        image_file = request.files.get('image')

        if not all([name, category, price_per_day, stock]):
            flash('Please fill all required fields.', 'danger')
            return render_template('admin/admin_add_gadget.html')

        # Default image
        image_path = "default_gadget.png"

        # If uploaded image exists → save it
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"uploads/{filename}"

        # Create gadget
        new_gadget = Gadget(
            name=name,
            category=category,
            description=description,
            price_per_day=price_per_day,
            stock=stock,
            image=image_path
        )

        db.session.add(new_gadget)
        db.session.commit()

        flash(f"Gadget {name} added successfully!", "success")
        return redirect(url_for('admin_gadgets'))

    return render_template('admin/admin_add_gadget.html')

@app.route('/admin/gadgets/edit/<int:gadget_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_gadget(gadget_id):
    gadget = Gadget.query.get_or_404(gadget_id)

    # Auto-fix missing image file
    if gadget.image != "default_gadget.png":
        absolute_path = os.path.join(app.root_path, "static", gadget.image)
        if not os.path.exists(absolute_path):
            gadget.image = "default_gadget.png"
            db.session.commit()

    if request.method == 'POST':
        gadget.name = request.form.get('name')
        gadget.category = request.form.get('category')
        gadget.description = request.form.get('description')
        gadget.price_per_day = request.form.get('price_per_day', type=float)
        gadget.stock = request.form.get('stock', type=int)
        gadget.is_active = ('is_active' in request.form)

        image_file = request.files.get('image')

        # Upload new image
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(save_path)

            new_path = f"uploads/{filename}"

            # Delete old image (only if not default)
            if gadget.image != "default_gadget.png":
                old_path = os.path.join(app.root_path, "static", gadget.image)
                if os.path.exists(old_path):
                    os.remove(old_path)

            gadget.image = new_path

        db.session.commit()
        flash("Gadget updated successfully.", "success")
        return redirect(url_for("admin_gadgets"))

    return render_template("admin/admin_edit_gadget.html", gadget=gadget)

@app.route('/admin/gadget/<int:gadget_id>/toggle-featured')
@login_required
@admin_required
def admin_toggle_featured(gadget_id):
    gadget = Gadget.query.get_or_404(gadget_id)
    gadget.is_featured = not gadget.is_featured
    db.session.commit()

    msg = "added to Featured" if gadget.is_featured else "removed from Featured"
    flash(f"{gadget.name} {msg}.", "success")
    return redirect(url_for('admin_gadgets'))



@app.route('/admin/gadgets/delete/<int:gadget_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_gadget(gadget_id):
    gadget = Gadget.query.get_or_404(gadget_id)
    # Delete associated image file
    if gadget.image and gadget.image != url_for('static', filename='default_gadget.png'):
        try:
            image_path = os.path.join(app.root_path, gadget.image[1:])
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            app.logger.error(f"Error deleting gadget image: {e}")

    db.session.delete(gadget)
    db.session.commit()
    flash(f'Gadget {gadget.name} deleted successfully.', 'info')
    return redirect(url_for('admin_gadgets'))


if __name__ == '__main__':
    app.run(debug=True)
