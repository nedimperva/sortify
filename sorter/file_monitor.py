"""
File monitoring module for Downloads Sorter application.
Uses watchdog to detect new files in the monitored directory.
"""
import time
import logging
import threading
from pathlib import Path
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
    Starts a background thread to process detected files.
    """
    def __init__(self):
        self.logger = logging.getLogger("FileMonitor")
        self.config = load_config()
        self.observer = None
        self.handler = DownloadHandler()
        self.running = False
        self.stop_event = threading.Event()
        self.process_thread = None
        
    def start(self):
        """Start monitoring the downloads directory"""
        if self.running:
            self.logger.info("File monitor already running")
            return
            
        # Create a new observer instance
        self.observer = Observer()
        
        downloads_path = Path(self.config.get("source_folder", str(Path.home() / "Downloads")))
        self.observer.schedule(self.handler, str(downloads_path), recursive=False)
        
        # Reset stop event if needed
        if self.stop_event.is_set():
            self.stop_event.clear()
            
        self.observer.start()
        self.running = True
        self.logger.info(f"Started monitoring: {downloads_path}")
        
        # Start processing thread
        self.process_thread = threading.Thread(target=self._process_loop)
        self.process_thread.daemon = True
        self.process_thread.start()
        
    def stop(self):
        """Stop monitoring the downloads directory"""
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