"""
Sortify - Downloads Sorter Application
A modern, minimalist application to automatically organize your downloads folder.
"""
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from sorter.utils import setup_logging
from sorter.file_monitor import FileMonitor
from ui.main_window import MainWindow

def main():
    """Main entry point for the application"""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Sortify Downloads Sorter")
    
    # Initialize the file monitor
    file_monitor = FileMonitor()
    
    # Create the GUI application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for consistent cross-platform look
    
    # Create and show the main window
    window = MainWindow(file_monitor=file_monitor)
    window.show()
    
    # Start file monitoring
    file_monitor.start()
    logger.info("File monitoring started")
    
    # Run the application
    # The application will now minimize to system tray when closed
    exit_code = app.exec()
    
    # Cleanup on exit
    if file_monitor.is_running():
        file_monitor.stop()
        logger.info("File monitoring stopped")
        
    logger.info("Application terminated")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()