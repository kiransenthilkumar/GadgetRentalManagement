from app import app, db
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
    sample_names = ["Arun", "Kiran", "Siva", "Rahul", "Prakash"]

    for i, name in enumerate(sample_names):
        users.append(
            User(
                name=name,
                email=f"{name.lower()}@gmail.com",
                password=generate_password_hash("user123"),
                phone=f"98765432{i}1",
                is_admin=False,
                is_verified=True,
                address=f"{name} Home Street"
            )
        )

    db.session.add(admin_user)
    db.session.add_all(users)
    db.session.commit()
    print("Users created.")

    # -----------------------------------------------------------
    # 2️⃣ REAL GADGET DATA (7 each category)
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
            }
        ]
    }

    gadgets = []
    for category, items in real_gadgets.items():
        for item in items:
            gadgets.append(
                Gadget(
                    name=item["name"],
                    category=category,
                    description=item["description"],
                    price_per_day=item["price"],
                    stock=item["stock"],
                    image=f"/static/uploads/{item['image']}",
                    is_active=True,
                    is_featured=item.get("featured", False),
                    view_count=0,
                    rental_count=0,
                    avg_rating=0.0,
                    created_at=datetime.utcnow()
                )
            )

    db.session.add_all(gadgets)
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
                status=random.choice(["returned", "completed", "booked", "active"]),
                payment_status="paid",
                transaction_id=f"TXN{random.randint(10000,99999)}",
                created_at=datetime.utcnow() - timedelta(days=random.randint(2, 20))
            )
            all_orders.append(order)

    db.session.add_all(all_orders)
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
        reviews.append(
            Review(
                order_id=order.id,
                gadget_id=order.gadget_id,
                user_id=order.user_id,
                rating=random.randint(3, 5),
                comment=random.choice(comments),
                created_at=datetime.utcnow() - timedelta(days=1)
            )
        )

    db.session.add_all(reviews)
    db.session.commit()
    print("Reviews added.")

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
        entries.append(
            Feedback(
                user_id=random.choice(users).id,
                subject=f"Feedback #{i+1}",
                message=fb_texts[i],
                created_at=datetime.utcnow()
            )
        )

    db.session.add_all(entries)
    db.session.commit()
    print("Feedback entries added.")

    print("\nDEMO DATA SEEDING COMPLETE!")

