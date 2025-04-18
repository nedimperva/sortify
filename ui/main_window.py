"""
Main window for Downloads Sorter application.
"""
import os
import customtkinter as ctk
from pathlib import Path
from PIL import Image, ImageTk
from datetime import datetime
import threading
import tkinter as tk
import math

from sorter.file_sorter import FileSorter
from sorter.stats import SortingStats
from sorter.utils import load_config, save_config
from .tray_icon import SortifyTrayIcon

# Set appearance mode and default color theme
ctk.set_appearance_mode("system")  # "system", "dark", "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class MainWindow(ctk.CTk):
    """Main window class for Downloads Sorter application"""
    def __init__(self, file_monitor=None):
        super().__init__()
        
        self.file_monitor = file_monitor
        self.config = load_config()
        self.sorter = FileSorter()
        self.stats = SortingStats()
        self.tray_icon = None
        self.is_closing = False
        self.current_time_range = "month"  # Default time range for statistics
        
        # Configure window
        self.title("Sortify - Downloads Sorter")
        self.geometry("900x600")
        self.minsize(800, 550)
        
        # Intercept window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Load icons and resources
        self.load_resources()
        
        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create sidebar frame
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()
        
        # Create status bar
        self.create_status_bar()
        
        # Initialize system tray
        self.initialize_tray()

    def initialize_tray(self):
        """Initialize the system tray icon"""
        self.tray_icon = SortifyTrayIcon(self, self.file_monitor)
        
        # Run the tray icon in a separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def on_close(self):
        """Handle window close event - minimize to tray"""
        self.withdraw()  # Hide the window instead of destroying it
        
    def quit_app(self):
        """Completely exit the application"""
        self.is_closing = True
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Stop the file monitor if it's running
        if self.file_monitor and self.file_monitor.is_running():
            self.file_monitor.stop()
            
        # Destroy the window
        self.destroy()
        
    def load_resources(self):
        """Load icons and resources"""
        resource_dir = Path(__file__).parent / "resources"
        
        # Default to creating simple color blocks if resources are not available
        self.dashboard_icon = ctk.CTkImage(Image.new("RGB", (20, 20), color="#3498db"), size=(20, 20))
        self.settings_icon = ctk.CTkImage(Image.new("RGB", (20, 20), color="#2ecc71"), size=(20, 20))
        self.stats_icon = ctk.CTkImage(Image.new("RGB", (20, 20), color="#e74c3c"), size=(20, 20))
        self.folder_icon = ctk.CTkImage(Image.new("RGB", (20, 20), color="#f39c12"), size=(20, 20))
        
        # Try to load actual icons if they exist
        try:
            if resource_dir.exists():
                icon_files = {
                    "dashboard": resource_dir / "dashboard.png",
                    "settings": resource_dir / "settings.png",
                    "stats": resource_dir / "stats.png",
                    "folder": resource_dir / "folder.png"
                }
                
                for name, path in icon_files.items():
                    if path.exists():
                        if name == "dashboard":
                            self.dashboard_icon = ctk.CTkImage(Image.open(path), size=(20, 20))
                        elif name == "settings":
                            self.settings_icon = ctk.CTkImage(Image.open(path), size=(20, 20))
                        elif name == "stats":
                            self.stats_icon = ctk.CTkImage(Image.open(path), size=(20, 20))
                        elif name == "folder":
                            self.folder_icon = ctk.CTkImage(Image.open(path), size=(20, 20))
        except Exception as e:
            print(f"Error loading resources: {e}")
        
    def create_sidebar(self):
        """Create sidebar with navigation buttons"""
        # Create sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)  # Push everything up
        
        # App logo and title
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Sortify", 
                                      font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))
        
        # Navigation buttons
        self.nav_dashboard = ctk.CTkButton(self.sidebar_frame, corner_radius=5, height=40,
                                         text="Dashboard", image=self.dashboard_icon,
                                         fg_color="transparent", text_color=("gray10", "gray90"),
                                         hover_color=("gray70", "gray30"),
                                         anchor="w", command=self.show_dashboard)
        self.nav_dashboard.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.nav_stats = ctk.CTkButton(self.sidebar_frame, corner_radius=5, height=40,
                                     text="Statistics", image=self.stats_icon,
                                     fg_color="transparent", text_color=("gray10", "gray90"),
                                     hover_color=("gray70", "gray30"),
                                     anchor="w", command=self.show_statistics)
        self.nav_stats.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.nav_settings = ctk.CTkButton(self.sidebar_frame, corner_radius=5, height=40,
                                       text="Settings", image=self.settings_icon,
                                       fg_color="transparent", text_color=("gray10", "gray90"),
                                       hover_color=("gray70", "gray30"),
                                       anchor="w", command=self.show_settings)
        self.nav_settings.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        # App control buttons at bottom
        self.control_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.control_frame.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
        
        self.toggle_button = ctk.CTkSwitch(self.control_frame, text="Active", command=self.toggle_service)
        self.toggle_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Set the initial state of the toggle based on whether the monitor is running
        if self.file_monitor and self.file_monitor.is_running():
            self.toggle_button.select()
        
        # Appearance mode
        self.appearance_mode = ctk.CTkOptionMenu(self.sidebar_frame, values=["System", "Light", "Dark"],
                                                command=self.change_appearance_mode)
        self.appearance_mode.grid(row=6, column=0, padx=20, pady=(10, 20), sticky="s")
                     
    def create_main_content(self):
        """Create the main content area"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self, fg_color=("gray98", "gray10"))
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Create all content frames
        self.create_dashboard_frame()
        self.create_statistics_frame()
        self.create_settings_frame()
        
        # Start with dashboard
        self.show_dashboard()
        
    def create_dashboard_frame(self):
        """Create the dashboard content"""
        self.dashboard_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Header
        header = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="Dashboard", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        sort_now_btn = ctk.CTkButton(header, text="Sort Now", width=120, height=32, command=self.sort_now)
        sort_now_btn.pack(side="right")
        
        # Activity section
        activity_frame = ctk.CTkFrame(self.dashboard_frame)
        activity_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        activity_header = ctk.CTkFrame(activity_frame, fg_color="transparent")
        activity_header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(activity_header, text="Recent Activity", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        refresh_btn = ctk.CTkButton(activity_header, text="Refresh", width=80, height=24, 
                                 command=self.refresh_dashboard)
        refresh_btn.pack(side="right")
        
        # Recent activity list (scrollable)
        self.activity_list = ctk.CTkScrollableFrame(activity_frame, fg_color="transparent")
        self.activity_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Summary cards
        summary_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        summary_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Configure grid for the cards
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.columnconfigure(1, weight=1)
        summary_frame.columnconfigure(2, weight=1)
        
        # Create stat cards (will populate in refresh_dashboard)
        self.files_sorted_card = self.create_stat_card(summary_frame, "Files Sorted", "0", 0)
        self.space_saved_card = self.create_stat_card(summary_frame, "Space Saved", "0 B", 1)
        self.categories_card = self.create_stat_card(summary_frame, "Categories", str(len(self.config.get("categories", {}))), 2)
        
        # Initial refresh to populate with real data
        self.refresh_dashboard()
        
    def create_statistics_frame(self):
        """Create the statistics content"""
        self.statistics_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Header
        header = ctk.CTkFrame(self.statistics_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="Statistics", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        self.time_range_selector = ctk.CTkSegmentedButton(header, values=["Week", "Month", "Year"], 
                                                      command=self.change_time_range)
        self.time_range_selector.pack(side="right")
        self.time_range_selector.set("Month")
        
        # Main stat container with two columns
        stat_container = ctk.CTkFrame(self.statistics_frame, fg_color="transparent")
        stat_container.pack(fill="both", expand=True, padx=20, pady=10)
        stat_container.grid_columnconfigure(0, weight=2)
        stat_container.grid_columnconfigure(1, weight=3)
        stat_container.grid_rowconfigure(0, weight=1)
        
        # Left column - pie chart
        self.pie_frame = ctk.CTkFrame(stat_container)
        self.pie_frame.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        
        pie_header = ctk.CTkFrame(self.pie_frame, fg_color="transparent")
        pie_header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(pie_header, text="Files by Category", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        # Placeholder for pie chart
        self.pie_chart_frame = ctk.CTkFrame(self.pie_frame, fg_color="transparent")
        self.pie_chart_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Right column - bar chart
        self.bar_frame = ctk.CTkFrame(stat_container)
        self.bar_frame.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        
        bar_header = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        bar_header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(bar_header, text="Files Sorted by Month", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        # Placeholder for bar chart
        self.bar_chart_frame = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        self.bar_chart_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Initial refresh to populate with real data
        self.refresh_statistics()
        
    def create_settings_frame(self):
        """Create the settings content"""
        self.settings_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Header
        header = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="Settings", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        save_btn = ctk.CTkButton(header, text="Save", width=120, height=32, command=self.save_settings)
        save_btn.pack(side="right")
        
        # Settings content in a scrollable frame
        settings_scroll = ctk.CTkScrollableFrame(self.settings_frame)
        settings_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Folder settings section
        folder_section = ctk.CTkFrame(settings_scroll)
        folder_section.pack(fill="x", padx=0, pady=(0, 15))
        
        ctk.CTkLabel(folder_section, text="Folder Settings", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Source folder
        source_frame = ctk.CTkFrame(folder_section, fg_color="transparent")
        source_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(source_frame, text="Source Folder:").pack(side="left")
        self.source_entry = ctk.CTkEntry(source_frame, width=300)
        self.source_entry.pack(side="left", padx=10)
        self.source_entry.insert(0, self.config.get("source_folder", str(Path.home() / "Downloads")))
        
        source_btn = ctk.CTkButton(source_frame, text="Browse", width=100, image=self.folder_icon, 
                                 compound="left", command=self.browse_source)
        source_btn.pack(side="left")
        
        # Destination folder
        dest_frame = ctk.CTkFrame(folder_section, fg_color="transparent")
        dest_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(dest_frame, text="Destination:").pack(side="left")
        self.dest_entry = ctk.CTkEntry(dest_frame, width=300)
        self.dest_entry.pack(side="left", padx=10)
        self.dest_entry.insert(0, self.config.get("destination_folder", str(Path.home() / "Downloads")))
        
        dest_btn = ctk.CTkButton(dest_frame, text="Browse", width=100, image=self.folder_icon, 
                               compound="left", command=self.browse_destination)
        dest_btn.pack(side="left")
        
        # Behavior section
        behavior_section = ctk.CTkFrame(settings_scroll)
        behavior_section.pack(fill="x", padx=0, pady=(0, 15))
        
        ctk.CTkLabel(behavior_section, text="Behavior", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        options_frame = ctk.CTkFrame(behavior_section, fg_color="transparent")
        options_frame.pack(fill="x", padx=15, pady=5)
        
        self.startup_var = ctk.BooleanVar(value=self.config.get("run_at_startup", True))
        startup_cb = ctk.CTkCheckBox(options_frame, text="Run at Windows startup", variable=self.startup_var)
        startup_cb.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.notify_var = ctk.BooleanVar(value=self.config.get("show_notifications", True))
        notify_cb = ctk.CTkCheckBox(options_frame, text="Show notifications", variable=self.notify_var)
        notify_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Categories section
        categories_section = ctk.CTkFrame(settings_scroll)
        categories_section.pack(fill="x", padx=0, pady=(0, 15))
        
        cats_header = ctk.CTkFrame(categories_section, fg_color="transparent")
        cats_header.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(cats_header, text="Categories", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
                   
        add_cat_btn = ctk.CTkButton(cats_header, text="Add Category", width=130, height=28, 
                                  command=self.add_category)
        add_cat_btn.pack(side="right")
        
        # Category list
        self.cat_list_frame = ctk.CTkFrame(categories_section)
        self.cat_list_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Populate categories from config
        self.refresh_categories()

    def create_status_bar(self):
        """Create status bar at bottom of window"""
        self.status_bar = ctk.CTkFrame(self, height=25, corner_radius=0)
        self.status_bar.grid(row=1, column=1, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready | Last sort: Never")
        self.status_label.pack(side="left", padx=15)
        
        self.version_label = ctk.CTkLabel(self.status_bar, text="v1.0.0")
        self.version_label.pack(side="right", padx=15)

    def refresh_categories(self):
        """Refresh the categories list in settings"""
        # Clear existing categories
        for widget in self.cat_list_frame.winfo_children():
            widget.destroy()
            
        # Add categories from config
        for i, (cat_name, extensions) in enumerate(self.config.get("categories", {}).items()):
            self.create_category_item(self.cat_list_frame, cat_name, ", ".join(extensions), i)

    # Helper methods for UI components
    def create_stat_card(self, parent, title, value, column):
        """Create a statistics card in the dashboard"""
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=column, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13)).pack(pady=(15, 5))
        value_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=24, weight="bold"))
        value_label.pack(pady=(0, 15))
        
        return value_label
    
    def add_activity_item(self, parent, filename, category, time_ago):
        """Add an activity item to the list"""
        item = ctk.CTkFrame(parent, height=50, fg_color=("gray90", "gray20"))
        item.pack(fill="x", padx=5, pady=5)
        
        # File info
        info_frame = ctk.CTkFrame(item, fg_color="transparent")
        info_frame.pack(side="left", padx=15, fill="both", expand=True)
        
        ctk.CTkLabel(info_frame, text=filename, 
                   font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        details = ctk.CTkFrame(info_frame, fg_color="transparent")
        details.pack(fill="x", anchor="w")
        
        ctk.CTkLabel(details, text=category, 
                   font=ctk.CTkFont(size=12), 
                   text_color=("gray40", "gray60")).pack(side="left")
                   
        ctk.CTkLabel(details, text=" • ", 
                   font=ctk.CTkFont(size=12), 
                   text_color=("gray40", "gray60")).pack(side="left")
                   
        ctk.CTkLabel(details, text=time_ago, 
                   font=ctk.CTkFont(size=12), 
                   text_color=("gray40", "gray60")).pack(side="left")
    
    def create_category_item(self, parent, name, extensions, row):
        """Create a category item in settings"""
        frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        frame.pack(fill="x", padx=0, pady=5)
        
        # Category name
        ctk.CTkLabel(frame, text=name, 
                   font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15, pady=10)
        
        # Extensions list        
        ctk.CTkLabel(frame, text=extensions, 
                   text_color=("gray40", "gray60")).pack(side="left", padx=5)
        
        # Edit button
        edit_btn = ctk.CTkButton(frame, text="Edit", width=60, height=24, 
                               fg_color="transparent", border_width=1, 
                               command=lambda n=name: self.edit_category(n))
        edit_btn.pack(side="right", padx=(5, 15), pady=10)
        
    # UI navigation and action methods
    def show_dashboard(self):
        # Hide all frames
        self.statistics_frame.pack_forget()
        self.settings_frame.pack_forget()
        
        # Show dashboard
        self.dashboard_frame.pack(fill="both", expand=True)
        
        # Update active button
        self.nav_dashboard.configure(fg_color=("gray75", "gray25"))
        self.nav_stats.configure(fg_color="transparent")
        self.nav_settings.configure(fg_color="transparent")
        
    def show_statistics(self):
        # Hide all frames
        self.dashboard_frame.pack_forget()
        self.settings_frame.pack_forget()
        
        # Show statistics
        self.statistics_frame.pack(fill="both", expand=True)
        
        # Update active button
        self.nav_dashboard.configure(fg_color="transparent")
        self.nav_stats.configure(fg_color=("gray75", "gray25"))
        self.nav_settings.configure(fg_color="transparent")
        
    def show_settings(self):
        # Hide all frames
        self.dashboard_frame.pack_forget()
        self.statistics_frame.pack_forget()
        
        # Show settings
        self.settings_frame.pack(fill="both", expand=True)
        
        # Update active button
        self.nav_dashboard.configure(fg_color="transparent")
        self.nav_stats.configure(fg_color="transparent")
        self.nav_settings.configure(fg_color=("gray75", "gray25"))
    
    # Action handlers
    def toggle_service(self):
        """Toggle the background service on/off"""
        if not self.file_monitor:
            return
            
        state = "Active" if self.toggle_button.get() else "Paused"
        
        if state == "Active" and not self.file_monitor.is_running():
            self.file_monitor.start()
        elif state == "Paused" and self.file_monitor.is_running():
            self.file_monitor.stop()
            
        self.status_label.configure(text=f"{state} | Last sort: {datetime.now().strftime('%H:%M:%S')}")
    
    def sort_now(self):
        """Manually trigger sorting"""
        source_folder = self.config.get("source_folder", str(Path.home() / "Downloads"))
        if Path(source_folder).exists():
            success_count, error_count = self.sorter.sort_directory(source_folder)
            current_time = datetime.now().strftime('%H:%M:%S')
            self.status_label.configure(text=f"Active | Last sort: {current_time} | {success_count} files sorted")
    
    def save_settings(self):
        """Save application settings"""
        # Update config with values from UI
        self.config["source_folder"] = self.source_entry.get()
        self.config["destination_folder"] = self.dest_entry.get()
        self.config["run_at_startup"] = self.startup_var.get()
        self.config["show_notifications"] = self.notify_var.get()
        
        # Save config
        from sorter.utils import save_config, set_run_at_startup
        save_config(self.config)
        set_run_at_startup(self.config["run_at_startup"])
        
        # Restart file monitor with new settings if it's running
        if self.file_monitor and self.file_monitor.is_running():
            self.file_monitor.stop()
            self.file_monitor.start()
    
    def browse_source(self):
        """Browse for source folder"""
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            self.source_entry.delete(0, 'end')
            self.source_entry.insert(0, folder)
    
    def browse_destination(self):
        """Browse for destination folder"""
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            self.dest_entry.delete(0, 'end')
            self.dest_entry.insert(0, folder)
    
    def add_category(self):
        """Add a new category"""
        # Would open add category dialog in real implementation
        from tkinter import simpledialog
        
        name = simpledialog.askstring("Add Category", "Enter category name:")
        if name and name not in self.config.get("categories", {}):
            extensions = simpledialog.askstring("Add Category", "Enter file extensions (comma separated):")
            if extensions:
                ext_list = [x.strip() for x in extensions.split(",")]
                ext_list = [x if x.startswith(".") else f".{x}" for x in ext_list]
                
                # Update config
                if "categories" not in self.config:
                    self.config["categories"] = {}
                self.config["categories"][name] = ext_list
                
                # Refresh the UI
                self.refresh_categories()
    
    def edit_category(self, category_name):
        """Edit a category"""
        from tkinter import simpledialog
        
        if category_name in self.config.get("categories", {}):
            current_extensions = ", ".join(self.config["categories"][category_name])
            new_extensions = simpledialog.askstring("Edit Category", 
                                                 f"Edit extensions for {category_name}:", 
                                                 initialvalue=current_extensions)
            
            if new_extensions is not None:  # Cancel returns None
                ext_list = [x.strip() for x in new_extensions.split(",")]
                ext_list = [x if x.startswith(".") else f".{x}" for x in ext_list]
                
                # Update config
                self.config["categories"][category_name] = ext_list
                
                # Refresh the UI
                self.refresh_categories()
    
    def change_appearance_mode(self, new_appearance_mode):
        """Change the app appearance mode"""
        ctk.set_appearance_mode(new_appearance_mode.lower())
    
    # Dashboard and statistics methods
    def refresh_dashboard(self):
        """Refresh the dashboard with current statistics"""
        # Clear activity list
        for widget in self.activity_list.winfo_children():
            widget.destroy()
            
        # Get recent activity data
        recent_activity = self.stats.get_recent_activity(limit=10)
        
        if recent_activity:
            for activity in recent_activity:
                self.add_activity_item(
                    self.activity_list,
                    activity['filename'],
                    activity['category'],
                    activity['time_ago']
                )
        else:
            # Show placeholder message when no activity
            placeholder = ctk.CTkFrame(self.activity_list, height=100, fg_color="transparent")
            placeholder.pack(fill="both", expand=True, padx=5, pady=20)
            
            ctk.CTkLabel(placeholder, text="No recent activity", 
                       font=ctk.CTkFont(size=14),
                       text_color=("gray40", "gray60")).pack(pady=40)
        
        # Update summary statistics
        total_stats = self.stats.get_total_stats()
        
        self.files_sorted_card.configure(text=str(total_stats['total_files']))
        self.space_saved_card.configure(text=total_stats['total_size'])
        self.categories_card.configure(text=str(total_stats['category_count'] or len(self.config.get("categories", {}))))
    
    def refresh_statistics(self):
        """Refresh statistical visualizations"""
        # Clear existing charts
        for widget in self.pie_chart_frame.winfo_children():
            widget.destroy()
        for widget in self.bar_chart_frame.winfo_children():
            widget.destroy()
            
        # Get data for the current time range
        category_data = self.stats.get_category_distribution(self.current_time_range)
        monthly_data = self.stats.get_monthly_stats(months=6)
        
        # Draw pie chart if we have data
        if category_data:
            self.draw_pie_chart(self.pie_chart_frame, category_data)
        else:
            self.show_no_data_message(self.pie_chart_frame, "No category data available")
        
        # Draw bar chart if we have data
        if monthly_data:
            self.draw_bar_chart(self.bar_chart_frame, monthly_data)
        else:
            self.show_no_data_message(self.bar_chart_frame, "No monthly data available")
    
    def draw_pie_chart(self, parent, data):
        """Draw a simple pie chart showing file distribution by category"""
        # Create a canvas for the pie chart
        canvas_width, canvas_height = 300, 300
        canvas = ctk.CTkCanvas(parent, width=canvas_width, height=canvas_height, 
                             bg=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1]))
        canvas.pack(pady=10)
        
        # Get total count
        total_count = sum(item['count'] for item in data)
        if total_count == 0:
            self.show_no_data_message(parent, "No files sorted yet")
            return
        
        # Define colors for pie slices
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#7f8c8d']
        
        # Draw pie slices
        center_x, center_y = canvas_width / 2, canvas_height / 2
        radius = min(canvas_width, canvas_height) * 0.4
        start_angle = 0
        
        # Create legend
        legend_frame = ctk.CTkFrame(parent, fg_color="transparent")
        legend_frame.pack(fill="x", padx=15, pady=10)
        
        # Limit to top 7 categories for visualization
        display_data = data[:7] if len(data) > 7 else data
        
        for i, item in enumerate(display_data):
            percentage = item['count'] / total_count
            end_angle = start_angle + (360 * percentage)
            
            # Draw slice
            color = colors[i % len(colors)]
            canvas.create_arc(
                center_x - radius, center_y - radius, 
                center_x + radius, center_y + radius, 
                start=start_angle, extent=(360 * percentage),
                fill=color, outline="white", width=2
            )
            
            # Add legend item
            legend_item = ctk.CTkFrame(legend_frame, fg_color="transparent")
            legend_item.pack(anchor="w", padx=5, pady=2)
            
            # Color square
            color_square = ctk.CTkCanvas(legend_item, width=15, height=15, 
                                      bg=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1]))
            color_square.create_rectangle(0, 0, 15, 15, fill=color, outline="")
            color_square.pack(side="left", padx=(0, 5))
            
            # Label
            category_text = f"{item['category']}: {item['count']} ({int(percentage * 100)}%)"
            ctk.CTkLabel(legend_item, text=category_text, 
                       font=ctk.CTkFont(size=12)).pack(side="left")
            
            start_angle = end_angle
    
    def draw_bar_chart(self, parent, data):
        """Draw a bar chart showing files sorted by month"""
        # Skip if no data
        if not data or not any(month['categories'] for month in data):
            self.show_no_data_message(parent, "No monthly data available")
            return
        
        # Define colors for categories
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e']
        
        # Create a canvas for the bar chart
        canvas_width, canvas_height = 500, 300
        canvas = ctk.CTkCanvas(parent, width=canvas_width, height=canvas_height, 
                             bg=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1]))
        canvas.pack(pady=10, fill="both", expand=True)
        
        # Chart dimensions
        chart_top = 40
        chart_bottom = canvas_height - 60
        chart_left = 60
        chart_right = canvas_width - 20
        chart_height = chart_bottom - chart_top
        
        # Draw axes
        canvas.create_line(chart_left, chart_top, chart_left, chart_bottom, fill="gray")
        canvas.create_line(chart_left, chart_bottom, chart_right, chart_bottom, fill="gray")
        
        # Get all categories across all months
        all_categories = set()
        for month in data:
            all_categories.update(month['categories'].keys())
            
        # Filter to top 5 categories for visualization
        categories = list(all_categories)[:5]
        
        # Calculate maximum value for scaling
        max_value = 0
        for month in data:
            month_total = sum(month['categories'].get(cat, 0) for cat in categories)
            max_value = max(max_value, month_total)
            
        # If no data, display message and return
        if max_value == 0:
            self.show_no_data_message(parent, "No files sorted in this period")
            return
            
        # Round max value up to nearest multiple of 5
        max_value = math.ceil(max_value / 5) * 5
        
        # Draw y-axis scale
        for i in range(0, max_value + 1, max(1, max_value // 5)):
            y_pos = chart_bottom - (i / max_value) * chart_height
            canvas.create_line(chart_left - 5, y_pos, chart_left, y_pos, fill="gray")
            canvas.create_text(chart_left - 10, y_pos, text=str(i), anchor="e", fill="gray")
            
        # Calculate width for each month group
        month_width = (chart_right - chart_left) / len(data)
        bar_width = month_width * 0.7 / len(categories)  # Width of each bar
        
        # Draw bars and x-axis labels
        for month_idx, month_data in enumerate(data):
            month_center = chart_left + month_idx * month_width + month_width / 2
            
            # Draw month label
            canvas.create_text(
                month_center, chart_bottom + 20, 
                text=month_data['month'], 
                anchor="n",
                fill="gray"
            )
            
            # Draw bars for each category
            for cat_idx, category in enumerate(categories):
                value = month_data['categories'].get(category, 0)
                if value > 0:
                    # Calculate bar position
                    bar_height = (value / max_value) * chart_height
                    bar_left = month_center - (bar_width * len(categories) / 2) + cat_idx * bar_width
                    
                    # Draw the bar
                    canvas.create_rectangle(
                        bar_left, chart_bottom - bar_height,
                        bar_left + bar_width, chart_bottom,
                        fill=colors[cat_idx % len(colors)],
                        outline=""
                    )
        
        # Create legend
        legend_frame = ctk.CTkFrame(parent, fg_color="transparent")
        legend_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        for i, category in enumerate(categories):
            if i < len(colors):
                legend_item = ctk.CTkFrame(legend_frame, fg_color="transparent")
                legend_item.pack(side="left", padx=10)
                
                # Color square
                color_square = ctk.CTkCanvas(legend_item, width=15, height=15,
                                         bg=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1]))
                color_square.create_rectangle(0, 0, 15, 15, fill=colors[i], outline="")
                color_square.pack(side="left", padx=(0, 5))
                
                # Label
                ctk.CTkLabel(legend_item, text=category, 
                           font=ctk.CTkFont(size=11)).pack(side="left")
    
    def show_no_data_message(self, parent, message):
        """Show a message when no data is available for charts"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(frame, text=message, 
                   font=ctk.CTkFont(size=14),
                   text_color=("gray40", "gray60")).pack(expand=True)
    
    def change_time_range(self, value):
        """Change the time range for statistics"""
        self.current_time_range = value.lower()
        self.refresh_statistics()
    
    def _apply_appearance_mode(self, color):
        """Apply the current appearance mode to a color"""
        if ctk.get_appearance_mode().lower() == "dark":
            return color
        else:
            # Return a light color for light mode
            return "#f0f0f0"  # Or another appropriate light color