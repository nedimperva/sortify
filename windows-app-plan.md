# Windows Downloads Sorter Application Plan

## 1. Project Setup

### Dependencies
```
pip install PyQt6 watchdog psutil python-dateutil pillow pystray
```

### Project Structure
```
downloads_sorter/
├── main.py                # Entry point
├── config.json            # User configuration
├── sorter/
│   ├── __init__.py
│   ├── file_monitor.py    # Watchdog implementation
│   ├── file_sorter.py     # Sorting logic
│   └── utils.py           # Helper functions
├── ui/
│   ├── __init__.py
│   ├── main_window.py     # Main UI window
│   ├── settings_dialog.py # Configuration UI
│   ├── tray_icon.py       # System tray integration
│   └── resources/         # Icons and assets
└── tests/                 # Unit tests
```

## 2. Core Components Design

### File Monitor (file_monitor.py)
- Implement a watchdog `FileSystemEventHandler` to detect new files in the Downloads folder
- Track file creation and modification events
- Queue files for sorting after a brief delay to ensure downloads are complete

### File Sorter (file_sorter.py)
- Parse file metadata to determine creation date
- Identify file type based on extension and content
- Create appropriate directory structure (Year/Month/Category)
- Move files to their designated locations
- Handle edge cases (existing files, permissions, etc.)

### File Categories
1. **Documents** (.pdf, .docx, .xlsx, .txt, etc.)
2. **Images** (.jpg, .png, .gif, .svg, etc.)
3. **Videos** (.mp4, .mov, .avi, etc.)
4. **Audio** (.mp3, .wav, .flac, etc.)
5. **Archives** (.zip, .rar, .7z, etc.)
6. **Programs** (.exe, .msi, .app, etc.)
7. **Others** (anything not in above categories)

## 3. User Interface

### Main Window (main_window.py)
- Dashboard showing recent activity
- Statistics (files sorted by category, space saved)
- Settings button
- Minimize to tray button

### Settings Dialog (settings_dialog.py)
- Source folder selection (default: Downloads)
- Destination folder selection (default: same as Downloads)
- Category customization (add/remove/rename)
- Startup options (run at system startup)
- File exclusion patterns

### System Tray Integration (tray_icon.py)
- Status icon in system tray
- Right-click menu with:
  - Open main window
  - Pause/Resume sorting
  - Sort now (manual trigger)
  - Exit

## 4. Background Service Implementation

- Create a Windows service that runs in the background
- Use `pystray` to manage the system tray icon
- Implement start/stop/pause functionality
- Low resource usage when idle

## 5. User Configuration (config.json)

```json
{
  "source_folder": "C:\\Users\\username\\Downloads",
  "destination_folder": "C:\\Users\\username\\Downloads",
  "run_at_startup": true,
  "categories": {
    "Documents": [".pdf", ".docx", ".txt", ".xlsx"],
    "Images": [".jpg", ".png", ".gif", ".svg"],
    "Videos": [".mp4", ".mov", ".avi"],
    "Audio": [".mp3", ".wav", ".flac"],
    "Archives": [".zip", ".rar", ".7z"],
    "Programs": [".exe", ".msi", ".dmg"],
    "Others": []
  },
  "exclusions": ["partial", ".crdownload", ".part"],
  "min_file_size": 1024,
  "sort_delay": 5
}
```

## 6. Implementation Roadmap

### Phase 1: Core Functionality
1. Set up project structure
2. Implement file monitoring with Watchdog
3. Create basic sorting logic
4. Test core functionality with sample files

### Phase 2: User Interface
1. Design main window layout
2. Implement settings dialog
3. Create system tray integration
4. Add basic statistics and file activity log

### Phase 3: System Integration
1. Add auto-start capability
2. Implement proper logging
3. Create installer (optional: using PyInstaller)
4. Add notification system for important events

### Phase 4: Polish & Refinement
1. Improve error handling
2. Add drag-and-drop support
3. Implement file conflict resolution strategies
4. Add themes and visual customization

## 7. Code Examples

### Main Application Entry Point (main.py)

```python
import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.tray_icon import SystemTrayIcon
from sorter.file_monitor import FileMonitor

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("downloads_sorter.log"),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger("main")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Initialize the main window
    main_window = MainWindow()
    
    # Initialize the system tray
    tray_icon = SystemTrayIcon(main_window)
    tray_icon.show()
    
    # Start the file monitor
    file_monitor = FileMonitor()
    file_monitor.start()
    
    logger.info("Application started successfully")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

### File Monitor Implementation (file_monitor.py)

```python
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from .file_sorter import FileSorter
from .utils import load_config

class DownloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.logger = logging.getLogger("DownloadHandler")
        self.config = load_config()
        self.sorter = FileSorter()
        self.processing_queue = {}
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Skip files that match exclusion patterns
        for pattern in self.config["exclusions"]:
            if pattern in file_path.name:
                return
                
        # Add to processing queue with timestamp
        self.processing_queue[file_path] = time.time()
        self.logger.info(f"New file detected: {file_path}")
        
    def process_queue(self):
        current_time = time.time()
        files_to_remove = []
        
        for file_path, timestamp in self.processing_queue.items():
            # Only process files after delay (to ensure download completion)
            if current_time - timestamp > self.config["sort_delay"]:
                if file_path.exists() and file_path.stat().st_size > self.config["min_file_size"]:
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
    def __init__(self):
        self.logger = logging.getLogger("FileMonitor")
        self.config = load_config()
        self.observer = Observer()
        self.handler = DownloadHandler()
        self.running = False
        
    def start(self):
        downloads_path = Path(self.config["source_folder"])
        self.observer.schedule(self.handler, str(downloads_path), recursive=False)
        self.observer.start()
        self.running = True
        self.logger.info(f"Started monitoring: {downloads_path}")
        
        # Start processing thread
        import threading
        self.stop_event = threading.Event()
        self.process_thread = threading.Thread(target=self._process_loop)
        self.process_thread.daemon = True
        self.process_thread.start()
        
    def stop(self):
        if self.running:
            self.stop_event.set()
            self.observer.stop()
            self.observer.join()
            self.running = False
            self.logger.info("Stopped file monitoring")
            
    def _process_loop(self):
        while not self.stop_event.is_set():
            self.handler.process_queue()
            time.sleep(1)
```

## 8. Testing Plan

1. **Unit Tests**
   - Test file categorization logic
   - Test date extraction from files
   - Test path creation logic

2. **Integration Tests**
   - Test end-to-end file sorting
   - Test UI interaction with backend

3. **User Testing**
   - Test with various file types
   - Test with large numbers of files
   - Test on different Windows versions

## 9. Distribution and Deployment

1. **Packaging Options**
   - PyInstaller for creating standalone executable
   - Inno Setup for creating Windows installer

2. **Installer Features**
   - Desktop shortcut creation
   - Start menu entry
   - Registry entries for auto-start
   - Uninstaller

3. **Updates**
   - Consider implementing a simple update checker
   - Version tracking in config file
