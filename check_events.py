#!/usr/bin/env python
from server import app, db, Event
from datetime import datetime

with app.app_context():
    event_count = Event.query.count()
    print(f"\n=== DATABASE EVENTS CHECK ===")
    print(f"Total events in DB: {event_count}\n")
    
    if event_count > 0:
        events = Event.query.all()
        for i, event in enumerate(events, 1):
            print(f"Event {i}: {event.title}")
            print(f"  - ID: {event.id}")
            print(f"  - Description: {event.description[:50]}...")
            print(f"  - start_datetime: {event.start_datetime}")
            print(f"  - end_datetime: {event.end_datetime}")
            print(f"  - event_date: {event.event_date}")
            print(f"  - Location: {event.location}")
            print(f"  - Published: {event.published}")
            print(f"  - Created: {event.created_at}\n")
    else:
        print("❌ No events found in database\n")
    
    # Check route query
    print("=== CHECKING INDEX ROUTE QUERY ===")
    upcoming = Event.query.filter(
        Event.start_datetime >= datetime.utcnow()
    ).limit(3).all()
    print(f"Upcoming events (query result): {len(upcoming)}")
    for event in upcoming:
        print(f"  - {event.title}: {event.start_datetime}")
