"""
Sortify - Downloads Sorter Application
A modern, minimalist application to automatically organize your downloads folder.
"""
import sys
import logging
from pathlib import Path
import customtkinter as ctk
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
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    
    # Create and show the main window
    app = MainWindow(file_monitor=file_monitor)
    
    # Start file monitoring
    file_monitor.start()
    logger.info("File monitoring started")
    
    # Run the application
    # The application will now minimize to system tray when closed
    app.mainloop()
    
    # Cleanup on exit
    if file_monitor.is_running():
        file_monitor.stop()
        logger.info("File monitoring stopped")
        
    logger.info("Application terminated")

if __name__ == "__main__":
    main()