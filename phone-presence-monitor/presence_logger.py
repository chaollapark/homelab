"""
Presence Logger - Logs phone arrival/departure times to CSV for pattern analysis.
"""

import csv
import os
from datetime import datetime
from pathlib import Path


class PresenceLogger:
    """Logs presence events to CSV file for historical analysis."""
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = Path(__file__).parent / "logs"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "presence_history.csv"
        self._ensure_csv_header()
    
    def _ensure_csv_header(self):
        """Create CSV file with header if it doesn't exist."""
        if not self.log_file.exists():
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'date',
                    'time', 
                    'day_of_week',
                    'event',
                    'phone_name',
                    'ip_address'
                ])
    
    def log_event(self, event: str, phone_name: str, ip_address: str):
        """
        Log a presence event.
        
        Args:
            event: 'arrived' or 'left'
            phone_name: Name of the phone
            ip_address: IP address of the phone
        """
        now = datetime.now()
        
        row = [
            now.isoformat(),
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M:%S'),
            now.strftime('%A'),  # Day name (Monday, Tuesday, etc.)
            event,
            phone_name,
            ip_address
        ]
        
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    
    def log_arrived(self, phone_name: str, ip_address: str):
        """Log phone arrival."""
        self.log_event('arrived', phone_name, ip_address)
    
    def log_left(self, phone_name: str, ip_address: str):
        """Log phone departure."""
        self.log_event('left', phone_name, ip_address)
    
    def get_stats(self) -> dict:
        """Get basic statistics from the log."""
        if not self.log_file.exists():
            return {'total_events': 0}
        
        arrivals = 0
        departures = 0
        days = set()
        
        with open(self.log_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['event'] == 'arrived':
                    arrivals += 1
                elif row['event'] == 'left':
                    departures += 1
                days.add(row['date'])
        
        return {
            'total_events': arrivals + departures,
            'arrivals': arrivals,
            'departures': departures,
            'days_tracked': len(days)
        }
