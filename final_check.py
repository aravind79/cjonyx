#!/usr/bin/env python
from server import app, db, Event
from datetime import datetime

with app.app_context():
    print("=== FINAL VERIFICATION ===\n")
    
    all_events = Event.query.filter(Event.published == True).all()
    print(f"Total published events: {len(all_events)}\n")
    
    # Simulate the index route logic
    upcoming_events = []
    now = datetime.utcnow()
    
    for event in all_events:
        event_start = event.start_datetime or event.event_date
        if event_start and now < event_start:
            upcoming_events.append(event)
            print(f"✅ {event.title}")
            print(f"   Start: {event_start}")
            print(f"   Status: UPCOMING\n")
        else:
            print(f"❌ {event.title}")
            print(f"   Start: {event_start}")
            print(f"   Status: PAST\n")
    
    upcoming_events = sorted(upcoming_events, key=lambda e: e.start_datetime or e.event_date)[:2]
    print(f"\n📌 Events to display on index page: {len(upcoming_events)}")
    for event in upcoming_events:
        print(f"   - {event.title}")
