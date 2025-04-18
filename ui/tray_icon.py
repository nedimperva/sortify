"""
System tray integration for Sortify application.
"""
import os
from pathlib import Path
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtCore import Qt
from datetime import datetime

class SortifyTrayIcon:
    """
    System tray icon for Sortify application.
    Allows app to run in background and provides quick access to common actions.
    """
    def __init__(self, app_instance, file_monitor=None):
        self.app_instance = app_instance
        self.file_monitor = file_monitor
        self.tray_icon = None
        self._create_icon()
        
    def _create_icon(self):
        """Create the system tray icon with menu"""
        # Try to load an icon file if available
        icon_path = Path(__file__).parent / "resources" / "sortify_icon.png"
        if icon_path.exists():
            try:
                icon = QIcon(str(icon_path))
            except Exception:
                # Use a colored icon as fallback
                pixmap = QPixmap(64, 64)
                pixmap.fill(Qt.GlobalColor.blue)
                icon = QIcon(pixmap)
        else:
            # Use a colored icon as fallback
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.blue)
            icon = QIcon(pixmap)
                
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Sortify")
        
        # Create menu
        self._create_menu()
                                 
    def _create_menu(self):
        """Create the tray icon context menu"""
        menu = QMenu()
        
        # Show the app status at the top of the menu
        self.status_action = QAction("Status: Ready", self.tray_icon)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)

        # Add a separator after status
        menu.addSeparator()
        
        # Open Sortify
        open_action = QAction("Open Sortify", self.tray_icon)
        open_action.triggered.connect(self._show_window)
        menu.addAction(open_action)
        
        # Sort Now
        sort_now_action = QAction("Sort Now", self.tray_icon)
        sort_now_action.triggered.connect(self._sort_now)
        menu.addAction(sort_now_action)
        
        menu.addSeparator()
        
        # Toggle monitoring (Pause/Resume)
        self.toggle_action = QAction("", self.tray_icon)
        self.toggle_action.setCheckable(True)
        self.toggle_action.setChecked(self._is_active())
        self.toggle_action.triggered.connect(self._toggle_service)
        
        # Set the initial text based on state
        if self._is_active():
            self.toggle_action.setText("Pause Monitoring")
            # Also update the status action
            self._update_status("Active")
        else:
            self.toggle_action.setText("Resume Monitoring")
            self._update_status("Paused")
            
        menu.addAction(self.toggle_action)
        
        # Theme submenu
        theme_menu = QMenu("Theme", menu)
        
        theme_system = QAction("System", theme_menu)
        theme_system.triggered.connect(lambda: self._change_theme("System"))
        theme_menu.addAction(theme_system)
        
        theme_light = QAction("Light", theme_menu)
        theme_light.triggered.connect(lambda: self._change_theme("Light"))
        theme_menu.addAction(theme_light)
        
        theme_dark = QAction("Dark", theme_menu)
        theme_dark.triggered.connect(lambda: self._change_theme("Dark"))
        theme_menu.addAction(theme_dark)
        
        menu.addMenu(theme_menu)
        
        menu.addSeparator()
        
        # Exit
        exit_action = QAction("Exit", self.tray_icon)
        exit_action.triggered.connect(self._exit_app)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)

    def update_toggle_state(self, is_active):
        """Update the toggle action's text and checked state from the main window."""
        if hasattr(self, 'toggle_action'):
            self.toggle_action.setChecked(is_active)
            if is_active:
                self.toggle_action.setText("Pause Monitoring")
                self._update_status("Active")
            else:
                self.toggle_action.setText("Resume Monitoring")
                self._update_status("Paused")
        
    def _update_status(self, status_text, details=None):
        """Update status text in tray menu"""
        if not hasattr(self, 'status_action'):
            return
            
        if details:
            self.status_action.setText(f"Status: {status_text} | {details}")
        else:
            self.status_action.setText(f"Status: {status_text}")
    
    def _show_window(self):
        """Show the main application window"""
        self.app_instance.show()
        self.app_instance.activateWindow()
        self.app_instance.raise_()
    
    def _sort_now(self):
        """Trigger manual sort"""
        if hasattr(self.app_instance, 'sort_now'):
            self.app_instance.sort_now()
            # Update the status to show sorting occurred
            current_time = datetime.now().strftime('%H:%M:%S')
            self._update_status("Active", f"Last sort: {current_time}")
    
    def _toggle_service(self):
        """Toggle the monitoring service on/off"""
        if hasattr(self.app_instance, 'toggle_service'):
            was_checked = self.app_instance.toggle_button.isChecked()
            self.app_instance.toggle_service()
            # Toggle the checkbox state, which triggers the main window's toggle_service
            self.app_instance.toggle_button.setChecked(not was_checked)
            # The main window's toggle_service will call back update_toggle_state
            # So no need to update text/status directly here anymore.

    def _is_active(self):
        """Check if monitoring service is active"""
        try:
            if hasattr(self.app_instance, 'toggle_button'):
                return self.app_instance.toggle_button.isChecked()
        except:
            pass
        return True
    
    def _change_theme(self, theme):
        """Change the app theme"""
        if hasattr(self.app_instance, 'change_appearance_mode'):
            self.app_instance.change_appearance_mode(theme)
    
    def _exit_app(self):
        """Exit the application completely"""
        self.app_instance.quit_app()
    
    def run(self):
        """Show the tray icon"""
        # Set initial state now that app_instance should be ready
        is_active = self._is_active()
        self.toggle_action.setChecked(is_active)
        self.toggle_action.triggered.connect(self._toggle_service) # Connect signal here
        # Call update_toggle_state to set initial text and status correctly
        self.update_toggle_state(is_active)

        self.tray_icon.show()

    def stop(self):
        """Hide the tray icon"""
        if self.tray_icon:
            self.tray_icon.hide()