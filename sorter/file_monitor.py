"""
File monitoring module for Downloads Sorter application.
Uses watchdog to detect new files in the monitored directory.
"""
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .file_sorter import FileSorter
from .utils import load_config

class DownloadHandler(FileSystemEventHandler):
    """
    Handler for file system events.
    Detects new downloads and queues them for sorting.
    """
    def __init__(self):
        self.logger = logging.getLogger("DownloadHandler")
        self.config = load_config()
        self.sorter = FileSorter()
        self.processing_queue = {}
        
    def on_created(self, event):
        """Called when a file is created in the monitored directory"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Skip files that match exclusion patterns
        for pattern in self.config.get("exclusions", []):
            if pattern in file_path.name:
                return
                
        # Add to processing queue with timestamp
        self.processing_queue[file_path] = time.time()
        self.logger.info(f"New file detected: {file_path}")
        
    def process_queue(self):
        """Process files in queue after delay to ensure download completion"""
        current_time = time.time()
        files_to_remove = []
        
        for file_path, timestamp in list(self.processing_queue.items()):
            # Only process files after delay (to ensure download completion)
            delay = self.config.get("sort_delay", 5)
            if current_time - timestamp > delay:
                min_size = self.config.get("min_file_size", 1024)
                if file_path.exists() and file_path.stat().st_size > min_size:
                    try:
                        self.sorter.sort_file(file_path)
                        files_to_remove.append(file_path)
                    except Exception as e:
                        self.logger.error(f"Error sorting {file_path}: {e}")
                else:
                    # Remove non-existent or too small files
                    files_to_remove.append(file_path)
                    
        # Remove processed files from queue
        for file_path in files_to_remove:
            self.processing_queue.pop(file_path, None)

class FileMonitor:
    """
    Monitors the downloads directory for new files.
    Supports both regular monitoring and scheduled scanning.
    """
    def __init__(self):
        self.logger = logging.getLogger("FileMonitor")
        self.config = load_config()
        self.observer = None
        self.handler = DownloadHandler()
        self.running = False
        self.stop_event = threading.Event()
        self.process_thread = None
        self.scheduler_thread = None
        self.last_scan_time = None
        self.missed_schedules = []
        
    def start(self):
        """Start the appropriate monitoring mode based on config"""
        if self.running:
            self.logger.info("File monitor already running")
            return
            
        # Reset stop event if needed
        if self.stop_event.is_set():
            self.stop_event.clear()
            
        scan_mode = self.config.get("scan_mode", "regular")
        self.running = True
        
        if scan_mode == "regular":
            self._start_regular_monitoring()
        else:  # scheduled mode
            self._start_scheduled_monitoring()
            
        self.logger.info(f"Started file monitor in {scan_mode} mode")
        
    def _start_regular_monitoring(self):
        """Start continuous file monitoring using watchdog"""
        # Create a new observer instance for regular monitoring
        self.observer = Observer()
        
        downloads_path = Path(self.config.get("source_folder", str(Path.home() / "Downloads")))
        self.observer.schedule(self.handler, str(downloads_path), recursive=False)
        
        self.observer.start()
        
        # Start processing thread
        self.process_thread = threading.Thread(target=self._process_loop)
        self.process_thread.daemon = True
        self.process_thread.start()
            
    def _start_scheduled_monitoring(self):
        """Start scheduled monitoring mode"""
        # Start the scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        # Check for missed scans if coming back online
        if self.config.get("scan_when_back_online", True):
            self._check_missed_schedules()
            
    def _scheduler_loop(self):
        """Background loop to run scheduled scans"""
        while not self.stop_event.is_set():
            # Check if current time matches any scheduled time
            current_time = datetime.now()
            scheduled_times = self.config.get("scheduled_times", [])
            
            for time_str in scheduled_times:
                try:
                    # Parse scheduled time
                    hour, minute = map(int, time_str.split(':'))
                    scheduled_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # If current time is within 59 seconds of scheduled time and we haven't run yet
                    time_diff = abs((current_time - scheduled_time).total_seconds())
                    
                    if time_diff < 60 and (self.last_scan_time is None or 
                                          (current_time - self.last_scan_time).total_seconds() > 60):
                        self._run_scheduled_scan()
                        # Update last scan time
                        self.last_scan_time = current_time
                        # Add to list of completed schedules
                        self._add_completed_schedule(scheduled_time)
                        break
                except Exception as e:
                    self.logger.error(f"Error processing scheduled scan at {time_str}: {e}")
            
            # Sleep for 30 seconds before next check
            time.sleep(30)
            
    def _run_scheduled_scan(self):
        """Run a scheduled scan of the source directory"""
        self.logger.info("Running scheduled scan")
        source_folder = self.config.get("source_folder", str(Path.home() / "Downloads"))
        success_count = 0 # Initialize counts
        error_count = 0   # Initialize counts

        try:
            # Use the file sorter to sort the entire directory
            sorter = FileSorter()
            success_count, error_count = sorter.sort_directory(source_folder) # Get the counts
            self.logger.info(f"Scheduled scan completed: {success_count} files sorted, {error_count} errors")
        except Exception as e:
            self.logger.error(f"Error during scheduled scan: {e}")
            # error_count might be implicitly 0 here, or could be set if needed

        return success_count, error_count # Return the counts

    def _check_missed_schedules(self):
        """Check for any scheduled scans that were missed while offline"""
        if not self.config.get("scan_when_back_online", True):
            return
            
        current_time = datetime.now()
        scheduled_times = self.config.get("scheduled_times", [])
        completed_schedules = self.config.get("completed_schedules", [])
        
        # Get the most recent completed schedule time
        last_completed = None
        if completed_schedules:
            try:
                last_completed = datetime.fromisoformat(completed_schedules[-1])
            except (ValueError, IndexError):
                pass
                
        # If we have no record of completed schedules, don't try to catch up
        if not last_completed:
            return
            
        # Check each scheduled time to see if we missed any
        for time_str in scheduled_times:
            try:
                # Parse scheduled time
                hour, minute = map(int, time_str.split(':'))
                
                # Check if there was a scheduled time between our last scan and now
                for days_ago in range(1, 8):  # Check up to a week back
                    check_date = current_time - timedelta(days=days_ago)
                    scheduled_datetime = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # If this scheduled time was after our last completion but before now,
                    # and we haven't already run it, then we missed it
                    if (last_completed < scheduled_datetime < current_time and 
                        scheduled_datetime.isoformat() not in completed_schedules):
                        self.missed_schedules.append(scheduled_datetime)
            except Exception as e:
                self.logger.error(f"Error checking for missed schedule {time_str}: {e}")
                
        # Run a scan now if we missed any schedules
        if self.missed_schedules:
            self.logger.info(f"Detected {len(self.missed_schedules)} missed scans, running catch-up scan now")
            self._run_scheduled_scan()
            # Mark all as completed
            for missed in self.missed_schedules:
                self._add_completed_schedule(missed)
            self.missed_schedules = []
            
    def _add_completed_schedule(self, scheduled_time):
        """Add a completed schedule to the tracking list"""
        if "completed_schedules" not in self.config:
            self.config["completed_schedules"] = []
            
        # Convert to ISO format string
        time_str = scheduled_time.isoformat()
        
        # Add to completed schedules
        if time_str not in self.config["completed_schedules"]:
            self.config["completed_schedules"].append(time_str)
            
        # Keep only last 50 completed schedules
        if len(self.config["completed_schedules"]) > 50:
            self.config["completed_schedules"] = self.config["completed_schedules"][-50:]
            
        # Save the updated config
        from .utils import save_config
        save_config(self.config)
        
    def stop(self):
        """Stop all monitoring"""
        if self.running:
            self.stop_event.set()
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            self.running = False
            self.logger.info("Stopped file monitoring")
            
    def _process_loop(self):
        """Background loop to process the file queue"""
        while not self.stop_event.is_set():
            self.handler.process_queue()
            time.sleep(1)
            
    def is_running(self):
        """Check if the monitor is currently running"""
        return self.running
        
    def scan_now(self):
        """Run a manual scan and return results"""
        source_folder = self.config.get("source_folder", str(Path.home() / "Downloads"))
        if not Path(source_folder).exists():
            self.logger.error(f"Source folder for scan_now not found: {source_folder}")
            return 0, 0 # Return zero counts if folder doesn't exist

        if self.running:
            # If monitor is running, use _run_scheduled_scan which now returns counts
            self.logger.info("Running manual scan via _run_scheduled_scan")
            return self._run_scheduled_scan()
        else:
            # If not running, perform a one-time scan directly
            self.logger.info("Running one-time manual scan")
            sorter = FileSorter()
            return sorter.sort_directory(source_folder)