
# Ensure upload folder exists
import os
os.makedirs(os.path.join(os.path.dirname(__file__), 'static', 'uploads'), exist_ok=True)
from app import app
from extensions import db
from models import User, Gadget, RentalOrder, Review, Feedback, Notification
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
import random

with app.app_context():

    # RESET DATABASE
    print("Clearing existing data...")
    db.drop_all()
    db.create_all()
    print("Database recreated.")

    # -----------------------------------------------------------
    # 1️⃣ CREATE USERS
    # -----------------------------------------------------------
    admin_user = User(
        name="Admin User",
        email="admin@gmail.com",
        password=generate_password_hash("admin123"),
        phone="9999999999",
        is_admin=True,
        is_verified=True,
        address="Admin Office Street"
    )

    users = []
    # 10 Tamil-style user names
    sample_names = [
        "Arun",
        "Karthik",
        "Prakash",
        "Sathish",
        "Vignesh",
        "Sowmiya",
        "Keerthana",
        "Hariharan",
        "Madhavan",
        "Nandhini",
    ]

    for i, name in enumerate(sample_names):
        user = User(
            name=name,
            email=f"{name.lower()}@gmail.com",
            password=generate_password_hash("user123"),
            phone=f"98765432{i}1",
            is_admin=False,
            is_verified=True,
            address=f"{name} Home Street"
        )
        db.session.add(user)
        users.append(user)

    db.session.add(admin_user)
    db.session.commit()
    print("Users created.")

    # -----------------------------------------------------------
    # 2️⃣ REAL GADGET DATA (at least 10 each category where possible)
    # -----------------------------------------------------------
    real_gadgets = {
        "Cameras & Photography": [
            {
                "name": "Sony A7 IV",
                "description": "Full-frame mirrorless camera designed for professionals.",
                "price": 1500, "stock": 5, "image": "sony_a7iv.jpg", "featured": True
            },
            {
                "name": "Canon R6 Mark II",
                "description": "Advanced autofocus and excellent low-light performance.",
                "price": 1400, "stock": 4, "image": "canon_r6_ii.jpg"
            },
            {
                "name": "Nikon Z6 II",
                "description": "Hybrid mirrorless camera for photography and videography.",
                "price": 1300, "stock": 3, "image": "nikon_z6ii.jpg"
            },
            {
                "name": "Fujifilm X-T5",
                "description": "40MP APS-C camera ideal for creators.",
                "price": 1000, "stock": 6, "image": "fuji_xt5.jpg"
            },
            {
                "name": "GoPro Hero 12",
                "description": "High-performance action camera for adventure lovers.",
                "price": 500, "stock": 10, "image": "gopro12.jpg"
            },
            {
                "name": "DJI Osmo Pocket 3",
                "description": "Compact stabilized 4K camera.",
                "price": 600, "stock": 8, "image": "osmo_pocket3.jpg"
            },
            {
                "name": "Blackmagic 6K Pro",
                "description": "Professional cinema camera for film production.",
                "price": 2000, "stock": 2, "image": "bmpcc6k.jpg"
            },
            {
                "name": "Sony ZV-E10",
                "description": "Compact vlogging camera with interchangeable lenses.",
                "price": 800, "stock": 6, "image": "sony_zve10.jpg"
            },
            {
                "name": "Canon EOS 90D",
                "description": "APS-C DSLR ideal for hybrid shooters.",
                "price": 900, "stock": 4, "image": "canon_90d.jpg"
            },
            {
                "name": "Instax Mini 12",
                "description": "Fun instant camera for events and parties.",
                "price": 250, "stock": 15, "image": "instax_mini12.jpg"
            }
        ],

        "Drones": [
            {
                "name": "DJI Mavic 3 Pro",
                "description": "Tri-camera drone with 5.1K recording.",
                "price": 1800, "stock": 3, "image": "mavic3pro.jpg", "featured": True
            },
            {
                "name": "DJI Mini 4 Pro",
                "description": "Compact lightweight drone with obstacle avoidance.",
                "price": 1000, "stock": 7, "image": "mini4pro.jpg"
            },
            {
                "name": "Autel EVO Lite+",
                "description": "1-inch sensor drone with long flight time.",
                "price": 1400, "stock": 2, "image": "evo_liteplus.jpg"
            },
            {
                "name": "DJI Air 3",
                "description": "Dual-camera drone with exceptional stability.",
                "price": 1300, "stock": 5, "image": "air3.jpg"
            },
            {
                "name": "FPV Racing Drone",
                "description": "High-speed FPV drone for freestyle.",
                "price": 1500, "stock": 1, "image": "fpv_drone.jpg"
            },
            {
                "name": "Parrot Anafi Thermal",
                "description": "Thermal drone for inspections.",
                "price": 2000, "stock": 2, "image": "anafi_thermal.jpg"
            },
            {
                "name": "Ryze Tello",
                "description": "Entry-level learning drone.",
                "price": 300, "stock": 12, "image": "tello.jpg"
            },
            {
                "name": "Mini CineWhoop",
                "description": "Indoor FPV cinewhoop drone.",
                "price": 900, "stock": 2, "image": "cinewhoop.jpg"
            },
            {
                "name": "DJI Avata",
                "description": "Immersive FPV drone with stabilised footage.",
                "price": 1600, "stock": 3, "image": "avata.jpg"
            },
            {
                "name": "Industrial Survey Drone",
                "description": "Long-range survey drone for mapping projects.",
                "price": 2500, "stock": 1, "image": "survey_drone.jpg"
            }
        ],

        "Gaming Consoles": [
            {
                "name": "PlayStation 5",
                "description": "Next-gen console with ray tracing and SSD speeds.",
                "price": 900, "stock": 6, "image": "ps5.jpg", "featured": True
            },
            {
                "name": "Xbox Series X",
                "description": "Microsoft’s most powerful gaming console.",
                "price": 850, "stock": 5, "image": "xbox_x.jpg"
            },
            {
                "name": "Nintendo Switch OLED",
                "description": "Hybrid gaming console with OLED display.",
                "price": 600, "stock": 10, "image": "switch_oled.jpg"
            },
            {
                "name": "Meta Quest 3",
                "description": "VR headset with mixed reality.",
                "price": 750, "stock": 4, "image": "quest3.jpg"
            },
            {
                "name": "Steam Deck OLED",
                "description": "Portable PC gaming handheld.",
                "price": 700, "stock": 3, "image": "steam_deck.jpg"
            },
            {
                "name": "PS4 Pro",
                "description": "4K gaming console with huge library.",
                "price": 500, "stock": 7, "image": "ps4pro.jpg"
            },
            {
                "name": "Retro Console Box",
                "description": "Emulator console with 10,000+ games.",
                "price": 350, "stock": 5, "image": "retro_console.jpg"
            },
            {
                "name": "Arcade Cabinet Mini",
                "description": "Tabletop arcade machine with classic titles.",
                "price": 450, "stock": 2, "image": "arcade_mini.jpg"
            },
            {
                "name": "Gaming PC RTX 4070",
                "description": "High-end desktop for 1440p competitive gaming.",
                "price": 1300, "stock": 3, "image": "gaming_pc_4070.jpg"
            },
            {
                "name": "Racing Wheel Bundle",
                "description": "Force-feedback wheel with pedals and shifter.",
                "price": 500, "stock": 4, "image": "racing_wheel.jpg"
            }
        ],

        "Laptops": [
            {
                "name": "MacBook Pro 16 M3 Max",
                "description": "Top-tier performance for editing and AI workloads.",
                "price": 1800, "stock": 4, "image": "mbp16_m3.jpg", "featured": True
            },
            {
                "name": "Dell XPS 13",
                "description": "Premium ultrabook with near edge-to-edge display.",
                "price": 1200, "stock": 5, "image": "xps13.jpg"
            },
            {
                "name": "HP Spectre x360",
                "description": "Convertible touch-screen laptop.",
                "price": 1000, "stock": 3, "image": "spectre.jpg"
            },
            {
                "name": "Razer Blade 15",
                "description": "Premium gaming laptop with RTX GPU.",
                "price": 1500, "stock": 2, "image": "razer15.jpg"
            },
            {
                "name": "Surface Laptop Studio",
                "description": "Creator-focused laptop with dynamic hinge.",
                "price": 1400, "stock": 3, "image": "surface_studio.jpg"
            },
            {
                "name": "Chromebook Plus",
                "description": "Lightweight device for basic tasks.",
                "price": 400, "stock": 8, "image": "chromebook.jpg"
            },
            {
                "name": "ThinkPad X1 Carbon",
                "description": "Business ultrabook with long battery life.",
                "price": 1300, "stock": 4, "image": "x1carbon.jpg"
            },
            {
                "name": "Asus ROG Zephyrus G14",
                "description": "Compact gaming laptop with powerful Ryzen CPU.",
                "price": 1400, "stock": 3, "image": "g14.jpg"
            },
            {
                "name": "MSI Creator Z16",
                "description": "Creator laptop with colour-accurate display.",
                "price": 1600, "stock": 2, "image": "creator_z16.jpg"
            },
            {
                "name": "Lenovo Legion 5",
                "description": "Balanced gaming laptop for students and pros.",
                "price": 1100, "stock": 5, "image": "legion5.jpg"
            }
        ]
    }

    gadgets = []
    for category, items in real_gadgets.items():
        for item in items:
            gadget = Gadget(
                name=item["name"],
                category=category,
                description=item["description"],
                price_per_day=item["price"],
                stock=item["stock"],
                # store relative path; missing files will fall back to default via ensure_images_valid()
                image=f"uploads/{item['image']}",
                is_active=True,
                is_featured=item.get("featured", False),
                view_count=0,
                rental_count=0,
                avg_rating=0.0,
                created_at=datetime.utcnow()
            )
            db.session.add(gadget)
            gadgets.append(gadget)

    db.session.commit()
    print(f"{len(gadgets)} gadgets inserted.")

    # -----------------------------------------------------------
    # 3️⃣ ORDERS (2–3 per user)
    # -----------------------------------------------------------
    all_orders = []
    today = date.today()

    for user in users:
        for _ in range(random.randint(2, 3)):
            gadget = random.choice(gadgets)

            start = today - timedelta(days=random.randint(5, 15))
            end = start + timedelta(days=random.randint(2, 6))
            days = (end - start).days

            order = RentalOrder(
                user_id=user.id,
                gadget_id=gadget.id,
                start_date=start,
                end_date=end,
                total_days=days,
                total_price=days * gadget.price_per_day,
                security_deposit=random.randint(500, 2000),
                status=random.choice(["returned", "booked", "active"]),
                payment_status="paid",
                transaction_id=f"TXN{random.randint(10000,99999)}",
                created_at=datetime.utcnow() - timedelta(days=random.randint(2, 20))
            )
            db.session.add(order)
            all_orders.append(order)
    db.session.commit()
    print("Orders created.")

    # -----------------------------------------------------------
    # 4️⃣ REVIEWS
    # -----------------------------------------------------------
    comments = [
        "Great quality!", "Very satisfied!", "Highly recommended!",
        "Could be better.", "Fantastic performance!"
    ]

    reviews = []
    for order in all_orders:
        review = Review(
            order_id=order.id,
            gadget_id=order.gadget_id,
            user_id=order.user_id,
            rating=random.randint(3, 5),
            comment=random.choice(comments),
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add(review)
        reviews.append(review)

    # Ensure every gadget has at least one review (even if it had no orders)
    for g in gadgets:
        has_review = any(r.gadget_id == g.id for r in reviews)
        if not has_review:
            user = random.choice(users)
            extra_review = Review(
                order_id=None,
                gadget_id=g.id,
                user_id=user.id,
                rating=random.randint(3, 5),
                comment=random.choice(comments),
                created_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(extra_review)
            reviews.append(extra_review)

    db.session.commit()
    print("Reviews added (including at least one per gadget).")

    # -----------------------------------------------------------
    # 5️⃣ UPDATE AVG RATING
    # -----------------------------------------------------------
    for g in gadgets:
        rlist = Review.query.filter_by(gadget_id=g.id).all()
        if rlist:
            g.avg_rating = sum(r.rating for r in rlist) / len(rlist)

    db.session.commit()
    print("Avg rating updated.")

    # -----------------------------------------------------------
    # 6️⃣ FEEDBACK
    # -----------------------------------------------------------
    fb_texts = [
        "Amazing service!", "Delivery was fast!", "Love the UI!",
        "More laptop models please.", "Support team is helpful."
    ]

    entries = []
    for i in range(5):
        fb = Feedback(
            user_id=random.choice(users).id,
            subject=f"Feedback #{i+1}",
            message=fb_texts[i],
            created_at=datetime.utcnow()
        )
        db.session.add(fb)
        entries.append(fb)
    db.session.commit()
    print("Feedback entries added.")

    # -----------------------------------------------------------
    # 7️⃣ NOTIFICATIONS (basic examples)
    # -----------------------------------------------------------
    notifs = []
    for u in users:
        notif = Notification(
            user_id=u.id,
            message="Welcome to GadgetRental! Your account is ready.",
            created_at=datetime.utcnow()
        )
        db.session.add(notif)
        notifs.append(notif)
    db.session.commit()
    print("Notifications added.")

    print("\nDEMO DATA SEEDING COMPLETE!")
