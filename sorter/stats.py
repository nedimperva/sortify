"""
Statistics tracking module for Downloads Sorter application.
Tracks file sorting statistics and provides methods to query them.
"""
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
from collections import defaultdict, Counter

class SortingStats:
    """
    Tracks and stores statistics about sorted files.
    Uses SQLite database for persistent storage.
    """
    def __init__(self):
        self.logger = logging.getLogger("SortingStats")
        self.db_path = Path.home() / ".sortify" / "statistics.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialize the SQLite database for statistics storage"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sorted_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT,
                    file_path TEXT,
                    category TEXT,
                    size_bytes INTEGER,
                    timestamp TIMESTAMP,
                    destination_path TEXT
                )
            ''')
            
            # Create summary table for faster queries
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    category TEXT,
                    count INTEGER,
                    total_size_bytes INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to initialize stats database: {e}")
    
    def record_sorted_file(self, file_path, category, destination_path):
        """Record a sorted file in the statistics database"""
        try:
            file_path = Path(file_path)
            size_bytes = file_path.stat().st_size if file_path.exists() else 0
            timestamp = datetime.now()
            date = timestamp.date()
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Record the sorted file
            cursor.execute('''
                INSERT INTO sorted_files 
                (file_name, file_path, category, size_bytes, timestamp, destination_path) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_path.name, str(file_path), category, size_bytes, timestamp, str(destination_path)))
            
            # Check if we have a summary entry for this date and category
            cursor.execute('''
                SELECT id, count, total_size_bytes FROM stats_summary 
                WHERE date = ? AND category = ?
            ''', (date.isoformat(), category))
            
            row = cursor.fetchone()
            if row:
                # Update existing summary
                cursor.execute('''
                    UPDATE stats_summary SET 
                    count = ?, total_size_bytes = ?
                    WHERE id = ?
                ''', (row[1] + 1, row[2] + size_bytes, row[0]))
            else:
                # Create new summary entry
                cursor.execute('''
                    INSERT INTO stats_summary
                    (date, category, count, total_size_bytes)
                    VALUES (?, ?, ?, ?)
                ''', (date.isoformat(), category, 1, size_bytes))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to record sorted file stats: {e}")
            return False
    
    def get_recent_activity(self, limit=10):
        """Get the most recently sorted files"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_name, category, timestamp 
                FROM sorted_files
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                file_time = datetime.fromisoformat(row['timestamp'])
                time_ago = self._format_time_ago(file_time)
                
                results.append({
                    'filename': row['file_name'],
                    'category': row['category'],
                    'time_ago': time_ago,
                    'timestamp': file_time
                })
                
            conn.close()
            return results
        except Exception as e:
            self.logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def get_total_stats(self):
        """Get overall statistics about sorted files"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Total files sorted
            cursor.execute('SELECT COUNT(*) FROM sorted_files')
            total_files = cursor.fetchone()[0] or 0
            
            # Total size of sorted files
            cursor.execute('SELECT SUM(size_bytes) FROM sorted_files')
            total_size = cursor.fetchone()[0] or 0
            
            # Count categories
            cursor.execute('SELECT COUNT(DISTINCT category) FROM sorted_files')
            category_count = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_files': total_files,
                'total_size': self._format_size(total_size),
                'total_size_bytes': total_size,
                'category_count': category_count
            }
        except Exception as e:
            self.logger.error(f"Failed to get total stats: {e}")
            return {
                'total_files': 0,
                'total_size': '0 B',
                'total_size_bytes': 0,
                'category_count': 0
            }
    
    def get_category_distribution(self, time_range='month'):
        """Get file distribution by category within the specified time range"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Calculate date range
            end_date = datetime.now()
            if time_range == 'week':
                start_date = end_date - timedelta(days=7)
            elif time_range == 'month':
                start_date = end_date - timedelta(days=30)
            elif time_range == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)  # Default to month
            
            # Query data
            cursor.execute('''
                SELECT category, COUNT(*) as count, SUM(size_bytes) as total_size
                FROM sorted_files
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY category
                ORDER BY count DESC
            ''', (start_date, end_date))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'category': row[0],
                    'count': row[1],
                    'size': self._format_size(row[2]),
                    'size_bytes': row[2] or 0
                })
                
            conn.close()
            return results
        except Exception as e:
            self.logger.error(f"Failed to get category distribution: {e}")
            return []
    
    def get_monthly_stats(self, months=6):
        """Get monthly statistics for the chart"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Calculate months to include
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30*months)
            
            # Get monthly data
            cursor.execute('''
                SELECT 
                    strftime('%Y-%m', timestamp) as month,
                    category,
                    COUNT(*) as count
                FROM sorted_files
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY month, category
                ORDER BY month
            ''', (start_date, end_date))
            
            results = defaultdict(lambda: defaultdict(int))
            for row in cursor.fetchall():
                month = row[0]  # Format: '2023-04'
                category = row[1]
                count = row[2]
                
                results[month][category] = count
                
            conn.close()
            
            # Convert to the required format for charting
            months_list = []
            current = start_date
            while current <= end_date:
                month_key = current.strftime('%Y-%m')
                months_list.append({
                    'month': current.strftime('%b %Y'),
                    'month_key': month_key,
                    'categories': dict(results[month_key])
                })
                
                # Advance to next month
                if current.month == 12:
                    current = datetime(current.year + 1, 1, 1)
                else:
                    current = datetime(current.year, current.month + 1, 1)
            
            return months_list
        except Exception as e:
            self.logger.error(f"Failed to get monthly stats: {e}")
            return []
    
    def _format_time_ago(self, timestamp):
        """Format a timestamp as a human-readable time ago string"""
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} {'year' if years == 1 else 'years'} ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} {'month' if months == 1 else 'months'} ago"
        elif diff.days > 0:
            return f"{diff.days} {'day' if diff.days == 1 else 'days'} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
        else:
            return "just now"
    
    def _format_size(self, size_bytes):
        """Format a file size in bytes to a human-readable format"""
        if size_bytes is None:
            return "0 B"
            
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024 or unit == 'TB':
                if unit == 'B':
                    return f"{size_bytes} {unit}"
                return f"{size_bytes:.2f} {unit}".rstrip('0').rstrip('.') + ' ' + unit
            size_bytes /= 1024.0