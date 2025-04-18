"""
Modern Minimalist UI Design for Downloads Sorter
Using CustomTkinter for clean, modern aesthetics
"""

import customtkinter as ctk
import os
from PIL import Image, ImageTk
from datetime import datetime

# Set appearance mode and default color theme
ctk.set_appearance_mode("system")  # "system", "dark", "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class DownloadsSorterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Downloads Sorter")
        self.geometry("900x600")
        self.minsize(800, 550)
        
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

    def load_resources(self):
        """Load icons and resources"""
        # Here you would load your actual icons
        self.dashboard_icon = ctk.CTkImage(Image.new("RGB", (20, 20), color="#3498db"), size=(20, 20))
        self.settings_icon = ctk.CTkImage(Image.new("RGB", (20, 20), color="#2ecc71"), size=(20, 20))
        self.stats_icon = ctk.CTkImage(Image.new("RGB", (20, 20), color="#e74c3c"), size=(20, 20))
        self.folder_icon = ctk.CTkImage(Image.new("RGB", (20, 20), color="#f39c12"), size=(20, 20))
        
    def create_sidebar(self):
        """Create sidebar with navigation buttons"""
        # Create sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)  # Push everything up
        
        # App logo and title
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Downloads Sorter", 
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
        self.toggle_button.select()  # Default to active
        
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
        
        # Recent activity list (scrollable)
        activity_list = ctk.CTkScrollableFrame(activity_frame, fg_color="transparent")
        activity_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Sample activities
        self.add_activity_item(activity_list, "vacation_photo.jpg", "Images", "2 minutes ago")
        self.add_activity_item(activity_list, "report_q1.pdf", "Documents", "15 minutes ago")
        self.add_activity_item(activity_list, "presentation.pptx", "Documents", "1 hour ago")
        self.add_activity_item(activity_list, "software_installer.exe", "Programs", "3 hours ago")
        
        # Summary cards
        summary_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        summary_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Configure grid for the cards
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.columnconfigure(1, weight=1)
        summary_frame.columnconfigure(2, weight=1)
        
        self.create_stat_card(summary_frame, "Files Sorted", "412", 0)
        self.create_stat_card(summary_frame, "Space Saved", "1.2 GB", 1)
        self.create_stat_card(summary_frame, "Categories", "7", 2)
        
    def create_statistics_frame(self):
        """Create the statistics content"""
        self.statistics_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Header
        header = ctk.CTkFrame(self.statistics_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="Statistics", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        time_range = ctk.CTkSegmentedButton(header, values=["Week", "Month", "Year"])
        time_range.pack(side="right")
        time_range.set("Month")
        
        # Main stat container with two columns
        stat_container = ctk.CTkFrame(self.statistics_frame, fg_color="transparent")
        stat_container.pack(fill="both", expand=True, padx=20, pady=10)
        stat_container.grid_columnconfigure(0, weight=2)
        stat_container.grid_columnconfigure(1, weight=3)
        stat_container.grid_rowconfigure(0, weight=1)
        
        # Left column - pie chart
        pie_frame = ctk.CTkFrame(stat_container)
        pie_frame.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        
        ctk.CTkLabel(pie_frame, text="Files by Category", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(padx=15, pady=15, anchor="w")
        
        # Placeholder for pie chart
        pie_chart = ctk.CTkCanvas(pie_frame, width=250, height=250)
        pie_chart.pack(pady=20)
        
        # Right column - bar chart
        bar_frame = ctk.CTkFrame(stat_container)
        bar_frame.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        
        ctk.CTkLabel(bar_frame, text="Files Sorted by Month", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(padx=15, pady=15, anchor="w")
        
        # Placeholder for bar chart
        bar_chart = ctk.CTkCanvas(bar_frame, width=400, height=300)
        bar_chart.pack(pady=20, fill="both", expand=True)
        
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
        source_entry = ctk.CTkEntry(source_frame, width=300)
        source_entry.pack(side="left", padx=10)
        source_entry.insert(0, os.path.expanduser("~/Downloads"))
        
        source_btn = ctk.CTkButton(source_frame, text="Browse", width=100, image=self.folder_icon, 
                                 compound="left", command=self.browse_source)
        source_btn.pack(side="left")
        
        # Destination folder
        dest_frame = ctk.CTkFrame(folder_section, fg_color="transparent")
        dest_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(dest_frame, text="Destination:").pack(side="left")
        dest_entry = ctk.CTkEntry(dest_frame, width=300)
        dest_entry.pack(side="left", padx=10)
        dest_entry.insert(0, os.path.expanduser("~/Downloads"))
        
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
        
        startup_var = ctk.BooleanVar(value=True)
        startup_cb = ctk.CTkCheckBox(options_frame, text="Run at Windows startup", variable=startup_var)
        startup_cb.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        notify_var = ctk.BooleanVar(value=True)
        notify_cb = ctk.CTkCheckBox(options_frame, text="Show notifications", variable=notify_var)
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
        cat_list = ctk.CTkFrame(categories_section)
        cat_list.pack(fill="x", padx=15, pady=(0, 15))
        
        categories = [
            ("Documents", [".pdf", ".docx", ".txt", ".xlsx"]),
            ("Images", [".jpg", ".png", ".gif", ".svg"]),
            ("Videos", [".mp4", ".mov", ".avi"]),
            ("Audio", [".mp3", ".wav", ".flac"]),
            ("Archives", [".zip", ".rar", ".7z"]),
            ("Programs", [".exe", ".msi", ".dmg"]),
        ]
        
        for i, (cat_name, extensions) in enumerate(categories):
            self.create_category_item(cat_list, cat_name, ", ".join(extensions), i)

    def create_status_bar(self):
        """Create status bar at bottom of window"""
        self.status_bar = ctk.CTkFrame(self, height=25, corner_radius=0)
        self.status_bar.grid(row=1, column=1, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready | Last sort: Never")
        self.status_label.pack(side="left", padx=15)
        
        self.version_label = ctk.CTkLabel(self.status_bar, text="v1.0.0")
        self.version_label.pack(side="right", padx=15)

    # Helper methods for UI components
    def create_stat_card(self, parent, title, value, column):
        """Create a statistics card in the dashboard"""
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=column, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13)).pack(pady=(15, 5))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 15))
    
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
                               command=lambda: self.edit_category(name))
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
        state = "Active" if self.toggle_button.get() else "Paused"
        self.status_label.configure(text=f"{state} | Last sort: {datetime.now().strftime('%H:%M:%S')}")
    
    def sort_now(self):
        """Manually trigger sorting"""
        # Would trigger actual sorting in real implementation
        self.status_label.configure(text=f"Active | Last sort: {datetime.now().strftime('%H:%M:%S')}")
    
    def save_settings(self):
        """Save application settings"""
        # Would save settings in real implementation
        pass
    
    def browse_source(self):
        """Browse for source folder"""
        # Would open folder dialog in real implementation
        pass
    
    def browse_destination(self):
        """Browse for destination folder"""
        # Would open folder dialog in real implementation
        pass
    
    def add_category(self):
        """Add a new category"""
        # Would open add category dialog in real implementation
        pass
    
    def edit_category(self, category_name):
        """Edit a category"""
        # Would open edit category dialog in real implementation
        pass
    
    def change_appearance_mode(self, new_appearance_mode):
        """Change the app appearance mode"""
        ctk.set_appearance_mode(new_appearance_mode.lower())


if __name__ == "__main__":
    app = DownloadsSorterApp()
    app.mainloop()
