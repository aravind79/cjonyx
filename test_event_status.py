#!/usr/bin/env python
from server import app, db, Event, get_event_status
from datetime import datetime, timedelta

with app.app_context():
    print("\n" + "="*80)
    print("EVENT STATUS VERIFICATION TEST")
    print("="*80 + "\n")
    
    current_time = datetime.utcnow()
    print(f"Current UTC Time: {current_time}\n")
    
    events = Event.query.filter_by(published=True).all()
    
    for i, event in enumerate(events, 1):
        status = get_event_status(event)
        start = event.start_datetime or event.event_date
        end = event.end_datetime
        
        print(f"{i}. {event.title}")
        print(f"   Start: {start}")
        print(f"   End:   {end}")
        print(f"   Status: {status.upper()}")
        
        # Detailed status reasoning
        if start and end:
            if current_time < start:
                print(f"   Reason: Current time ({current_time}) < Start time ({start})")
            elif start <= current_time <= end:
                print(f"   Reason: Current time ({current_time}) is between start and end")
            else:
                print(f"   Reason: Current time ({current_time}) > End time ({end})")
        elif start:
            if current_time < start:
                print(f"   Reason: Current time ({current_time}) < Start time ({start})")
            else:
                print(f"   Reason: Current time ({current_time}) >= Start time ({start})")
        
        print()
    
    print("="*80)
    print("\nSTATUS SUMMARY:")
    print("-" * 80)
    
    status_counts = {}
    for event in events:
        status = get_event_status(event)
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        print(f"  {status.upper()}: {count} event(s)")
    
    is_working = all(status != 'unknown' for status in status_counts.keys())
    print(f"\n[OK] Status logic is working correctly!" if is_working else "\n[WARNING] Some events have unknown status")
    print("\n" + "="*80 + "\n")
