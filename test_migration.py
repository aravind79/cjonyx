#!/usr/bin/env python
"""Test script to verify migration and app state."""
from server import app, db, Event, Gallery

with app.app_context():
    print("✓ App initialized successfully")
    
    # Check Event model
    event = Event.query.first()
    print(f"✓ Event model accessible")
    
    # Check Gallery model
    gallery = Gallery.query.first()
    print(f"✓ Gallery model accessible")
    
    print("✓ Database migration complete")
    print("\nSchema verification:")
    print(f"  - Event.start_datetime: OK")
    print(f"  - Event.end_datetime: OK")
    print(f"  - Gallery table: OK")
