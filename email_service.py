# email_service.py
# Safe for Windows consoles (fixes UnicodeEncodeError for ₹ symbol)

def safe_print(text: str):
    """
    Ensures console printing does NOT crash on Windows terminals
    that do not support the ₹ symbol or other Unicode characters.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # Remove unsupported characters
        print(text.encode("ascii", "ignore").decode())


def send_welcome_email(email, user_name):
    subject = "Welcome to Gadget Rental!"
    body = (
        f"Dear {user_name},\n\n"
        "Welcome to Gadget Rental! Your account has been created successfully.\n\n"
        "We are excited to have you on board.\n\n"
        "Best regards,\nThe Gadget Rental Team"
    )

    safe_print(f"Sending Welcome Email to: {email}")
    safe_print(f"Body:\n{body}")


def send_order_confirmation_email(email, user_name, order_id, gadget_name, total_price, start_date, end_date):
    subject = "Your Gadget Rental Order Confirmation"

    # Use INR instead of ₹ to avoid Unicode crash
    body = (
        f"Dear {user_name},\n\n"
        f"Your order for {gadget_name} (Order ID: {order_id}) has been successfully placed.\n"
        f"Rental Dates: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}.\n"
        f"Total Price: INR {total_price:.2f}.\n\n"
        "We will notify you once your order is approved.\n\n"
        "Best regards,\nThe Gadget Rental Team"
    )

    safe_print(f"Sending Order Confirmation Email to: {email}")
    safe_print(f"Body:\n{body}")


def send_payment_receipt_email(email, user_name, order_id, transaction_id, amount_paid):
    subject = "Payment Receipt – Gadget Rental"

    body = (
        f"Dear {user_name},\n\n"
        f"Your payment for Order ID {order_id} has been received successfully.\n"
        f"Transaction ID: {transaction_id}\n"
        f"Amount Paid: INR {amount_paid:.2f}\n\n"
        "Thank you for renting with us!\n\n"
        "Best regards,\nThe Gadget Rental Team"
    )

    safe_print(f"Sending Payment Receipt Email to: {email}")
    safe_print(f"Body:\n{body}")


def send_deposit_refund_confirmation_email(email, user_name, order_id, refund_amount):
    subject = "Security Deposit Refund Confirmation"

    body = (
        f"Dear {user_name},\n\n"
        f"Your security deposit for Order ID {order_id} has been refunded.\n"
        f"Refund Amount: INR {refund_amount:.2f}\n\n"
        "Thank you for using Gadget Rental!\n\n"
        "Best regards,\nThe Gadget Rental Team"
    )

    safe_print(f"Sending Deposit Refund Email to: {email}")
    safe_print(f"Body:\n{body}")
