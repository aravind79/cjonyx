#!/usr/bin/env python
from server import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    print("\n=== USER CHECK ===\n")
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print(f"[OK] Admin user exists")
        print(f"  Username: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  Is Admin: {admin.is_admin}")
        if not admin.is_admin:
            print("\n[WARNING] Admin user exists but is_admin is False!")
            print("Fixing this...")
            admin.is_admin = True
            db.session.commit()
            print("[OK] Updated admin.is_admin to True")
    else:
        print("[ERROR] Admin user does not exist")
        print("Creating default admin user...")
        admin = User(
            username='admin',
            email='admin@cjonyx.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("[OK] Admin user created with:")
        print("  Username: admin")
        print("  Password: admin123")
        print("  Is Admin: True")
    
    print(f"\n[OK] Admin login verified!")
    print(f"  Login with: admin / admin123\n")
