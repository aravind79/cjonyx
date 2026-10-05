#!/usr/bin/env python
from server import app, db, Event
from datetime import datetime, timedelta

with app.app_context():
    # Update existing events with future dates
    events = Event.query.all()
    
    base_date = datetime.utcnow()
    
    for i, event in enumerate(events):
        # Set future dates for each event
        days_ahead = 3 + (i * 7)  # 3, 10, 17 days from now
        new_start = base_date + timedelta(days=days_ahead)
        new_end = new_start + timedelta(hours=4)
        
        event.start_datetime = new_start
        event.end_datetime = new_end
        event.event_date = new_start  # Keep event_date in sync
        
        print(f"Updated: {event.title}")
        print(f"  Start: {event.start_datetime}")
        print(f"  End: {event.end_datetime}\n")
    
    db.session.commit()
    print("✅ All events updated with future dates!")
