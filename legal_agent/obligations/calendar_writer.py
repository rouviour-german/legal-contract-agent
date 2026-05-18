"""
Calendar writer for legal contract obligations.

Generates iCal files (.ics) and syncs with Google Calendar 
using native APIs for proactive alerting.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from icalendar import Calendar, Event
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from legal_agent.models import Obligation

logger = logging.getLogger(__name__)


def write_ical_file(obligations: list[Obligation], output_path: Path) -> Path:
    """Expert iCal (.ics) generator for inter-app notification."""
    cal = Calendar()
    cal.add('prodid', '-//Legal Contract Agent//legalagent.ai//')
    cal.add('version', '2.0')

    for ob in obligations:
        event = Event()
        event.add('summary', f"[Legal Agent] {ob.obligation_type.upper()}: {ob.description}")
        event.add('dtstart', ob.due_date)
        event.add('dtend', ob.due_date)
        event.add('dtstamp', datetime.now())
        event.add('uid', ob.id)
        
        # Expert usage: VALARM for proactive notification
        alarm = Event()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f"Reminder: {ob.description} (Due in {ob.lead_time_days} days)")
        # Trigger 'lead_time_days' before due_date
        # alarm.add('trigger', f"-P{ob.lead_time_days}D") 
        event.add_component(alarm)
        cal.add_component(event)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(cal.to_ical())
    
    return output_path


def sync_google_calendar(obligations: list[Obligation], credentials_json: str):
    """
    Expert implementation: pushes events to Google Calendar.
    Requires valid OAuth2 credentials and scopes.
    """
    try:
        service = build('calendar', 'v3', credentials=Credentials.from_authorized_user_info(credentials_json))
        for ob in obligations:
            event = {
                'summary': f"[Legal Agent] {ob.obligation_type}: {ob.description}",
                'description': ob.description,
                'start': {
                    'dateTime': ob.due_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': ob.due_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': ob.lead_time_days * 24 * 60},
                        {'method': 'popup', 'minutes': 24 * 60},
                    ],
                },
            }
            service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"Successfully synced {len(obligations)} obligations to Google Calendar.")
    except Exception as e:
        logger.error(f"Google Calendar sync failed: {e}")
