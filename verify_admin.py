#!/usr/bin/env python
from server import app, db, User
from werkzeug.security import check_password_hash

with app.app_context():
    print("\n=== ADMIN USER VERIFICATION ===\n")
    
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        print("[ERROR] Admin user not found!")
    else:
        print("[FOUND] Admin user details:")
        print(f"  ID: {admin.id}")
        print(f"  Username: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  is_admin field: {admin.is_admin}")
        print(f"  is_admin type: {type(admin.is_admin)}")
        
        # Test password
        pwd_correct = check_password_hash(admin.password_hash, 'admin123')
        print(f"  Password correct: {pwd_correct}")
        
        # Check all users
        print("\n[ALL USERS IN DATABASE]:")
        all_users = User.query.all()
        for u in all_users:
            print(f"  - {u.username}: is_admin={u.is_admin} (type: {type(u.is_admin).__name__})")
