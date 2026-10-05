#!/usr/bin/env python
"""Test login flow"""
from server import app, db, User
from werkzeug.security import check_password_hash

with app.app_context():
    print("\n=== LOGIN SIMULATION ===\n")
    
    # Simulate login
    username = 'admin'
    password = 'admin123'
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        print(f"[ERROR] User '{username}' not found")
    elif not check_password_hash(user.password_hash, password):
        print(f"[ERROR] Password incorrect for '{username}'")
    else:
        print(f"[OK] Login would succeed")
        print(f"  user.id = {user.id}")
        print(f"  user.username = {user.username}")
        print(f"  user.is_admin = {user.is_admin}")
        print(f"\n[Session values would be set to:]")
        print(f"  session['user_id'] = {user.id}")
        print(f"  session['username'] = '{user.username}'")
        print(f"  session['is_admin'] = {user.is_admin}")
        
        print(f"\n[Then admin_required decorator would check:]")
        # Simulate what decorator does
        test_user = User.query.get(user.id)
        print(f"  User.query.get(session['user_id']) = {test_user}")
        print(f"  user.is_admin = {test_user.is_admin}")
        print(f"  not user or not user.is_admin = {not test_user or not test_user.is_admin}")
        
        if not test_user or not test_user.is_admin:
            print(f"\n[ERROR] Decorator would deny access!")
        else:
            print(f"\n[OK] Decorator would allow access!")
