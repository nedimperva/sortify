"""
System tray integration for Sortify application.
"""
import os
import pystray
from PIL import Image
from pathlib import Path

class SortifyTrayIcon:
    """
    System tray icon for Sortify application.
    Allows app to run in background and provides quick access to common actions.
    """
    def __init__(self, app_instance, file_monitor=None):
        self.app_instance = app_instance
        self.file_monitor = file_monitor
        self.icon = None
        self._create_icon()
        
    def _create_icon(self):
        """Create the system tray icon with menu"""
        # Use a colored square as a fallback icon
        icon_image = Image.new('RGB', (64, 64), color="#3498db")
        
        # Try to load an icon file if available
        icon_path = Path(__file__).parent / "resources" / "sortify_icon.png"
        if icon_path.exists():
            try:
                icon_image = Image.open(icon_path)
            except Exception:
                pass
                
        self.icon = pystray.Icon("sortify", 
                                icon_image, 
                                "Sortify", 
                                menu=self._create_menu())
                                
    def _create_menu(self):
        """Create the tray icon context menu"""
        return pystray.Menu(
            pystray.MenuItem("Open Sortify", self._show_window),
            pystray.MenuItem("Sort Now", self._sort_now),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Pause/Resume", self._toggle_service, checked=lambda item: self._is_active()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._exit_app)
        )
        
    def _show_window(self, icon, item):
        """Show the main application window"""
        self.app_instance.deiconify()
        self.app_instance.lift()
        self.app_instance.focus_force()
    
    def _sort_now(self, icon, item):
        """Trigger manual sort"""
        if hasattr(self.app_instance, 'sort_now'):
            self.app_instance.sort_now()
    
    def _toggle_service(self, icon, item):
        """Toggle the monitoring service on/off"""
        if hasattr(self.app_instance, 'toggle_service'):
            self.app_instance.toggle_service()
        
    def _is_active(self):
        """Check if monitoring service is active"""
        try:
            if hasattr(self.app_instance, 'toggle_button'):
                return self.app_instance.toggle_button.get()
        except:
            pass
        return True
    
    def _exit_app(self, icon, item):
        """Exit the application completely"""
        icon.stop()
        self.app_instance.quit_app()
    
    def run(self):
        """Run the tray icon in a separate thread"""
        self.icon.run_detached()

    def stop(self):
        """Stop the tray icon"""
        if self.icon:
            self.icon.stop()