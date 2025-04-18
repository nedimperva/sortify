"""
Main window for Downloads Sorter application.
"""
import os
import sys
from pathlib import Path
from PIL import Image
from datetime import datetime
import threading
import math

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QFileDialog,
    QCheckBox, QRadioButton, QLineEdit, QMessageBox, QSplitter,
    QGridLayout, QStackedWidget, QComboBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot, QTimer
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QPalette, QPainter
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

from sorter.file_sorter import FileSorter
from sorter.stats import SortingStats
from sorter.utils import load_config, save_config
from .tray_icon import SortifyTrayIcon

class MainWindow(QMainWindow):
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
        self.setWindowTitle("Sortify - Downloads Sorter")
        self.resize(900, 600)
        self.setMinimumSize(800, 550)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Load icons and resources
        self.load_resources()
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()
        
        # Apply stylesheet (after all UI components are created)
        self.apply_stylesheet()
        
        # Apply saved theme if available
        saved_theme = self.config.get("appearance_mode", "System")
        if saved_theme:
            # Set the combobox to match the saved theme
            self.appearance_mode.setCurrentText(saved_theme.capitalize())
            # Apply the theme
            self.change_appearance_mode(saved_theme)
        
        # Initialize system tray
        self.initialize_tray()

    def closeEvent(self, event):
        """Intercept the window close event to minimize to tray instead of closing"""
        if self.is_closing:
            # If we're actually closing the app, accept the event
            event.accept()
        else:
            # Otherwise, hide the window and reject the close event
            self.hide()
            event.ignore()
            
    def initialize_tray(self):
        """Initialize the system tray icon"""
        self.tray_icon = SortifyTrayIcon(self, self.file_monitor)
        self.tray_icon.run()

    def on_close(self):
        """Handle window close event - minimize to tray"""
        self.hide()  # Hide the window instead of destroying it
        
    def quit_app(self):
        """Completely exit the application"""
        self.is_closing = True
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Stop the file monitor if it's running
        if self.file_monitor and self.file_monitor.is_running():
            self.file_monitor.stop()
            
        # Destroy the window
        self.close()
        
    def load_resources(self):
        """Load icons and resources"""
        resource_dir = Path(__file__).parent / "resources"
        
        # Default to creating simple pixmaps if resources are not available
        dashboard_pixmap = QPixmap(20, 20)
        dashboard_pixmap.fill(QColor("#3498db"))
        self.dashboard_icon = QIcon(dashboard_pixmap)
        
        settings_pixmap = QPixmap(20, 20)
        settings_pixmap.fill(QColor("#2ecc71"))
        self.settings_icon = QIcon(settings_pixmap)
        
        stats_pixmap = QPixmap(20, 20)
        stats_pixmap.fill(QColor("#e74c3c"))
        self.stats_icon = QIcon(stats_pixmap)
        
        folder_pixmap = QPixmap(20, 20)
        folder_pixmap.fill(QColor("#f39c12"))
        self.folder_icon = QIcon(folder_pixmap)
        
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
                            self.dashboard_icon = QIcon(str(path))
                        elif name == "settings":
                            self.settings_icon = QIcon(str(path))
                        elif name == "stats":
                            self.stats_icon = QIcon(str(path))
                        elif name == "folder":
                            self.folder_icon = QIcon(str(path))
        except Exception as e:
            print(f"Error loading resources: {e}")
        
    def create_sidebar(self):
        """Create sidebar with navigation buttons"""
        # Create sidebar frame
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setFixedWidth(200)
        self.sidebar_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.sidebar_frame.setFrameShadow(QFrame.Shadow.Raised)
        
        self.sidebar_layout = QVBoxLayout(self.sidebar_frame)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_layout.setSpacing(0)
        
        # App logo and title
        self.logo_label = QLabel("Sortify")
        self.logo_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setContentsMargins(0, 20, 0, 20)
        self.sidebar_layout.addWidget(self.logo_label)
        
        # Navigation buttons
        self.nav_dashboard = QPushButton("Dashboard")
        self.nav_dashboard.setIcon(self.dashboard_icon)
        self.nav_dashboard.setIconSize(QSize(20, 20))
        self.nav_dashboard.setFlat(True)
        self.nav_dashboard.setStyleSheet("text-align: left; padding: 10px;")
        self.nav_dashboard.clicked.connect(self.show_dashboard)
        self.sidebar_layout.addWidget(self.nav_dashboard)
        
        self.nav_stats = QPushButton("Statistics")
        self.nav_stats.setIcon(self.stats_icon)
        self.nav_stats.setIconSize(QSize(20, 20))
        self.nav_stats.setFlat(True)
        self.nav_stats.setStyleSheet("text-align: left; padding: 10px;")
        self.nav_stats.clicked.connect(self.show_statistics)
        self.sidebar_layout.addWidget(self.nav_stats)
        
        self.nav_settings = QPushButton("Settings")
        self.nav_settings.setIcon(self.settings_icon)
        self.nav_settings.setIconSize(QSize(20, 20))
        self.nav_settings.setFlat(True)
        self.nav_settings.setStyleSheet("text-align: left; padding: 10px;")
        self.nav_settings.clicked.connect(self.show_settings)
        self.sidebar_layout.addWidget(self.nav_settings)
        
        self.sidebar_layout.addStretch(1)
        
        # App control buttons at bottom
        self.control_frame = QFrame()
        self.control_layout = QVBoxLayout(self.control_frame)
        
        self.toggle_button = QCheckBox("Active")
        self.toggle_button.stateChanged.connect(self.toggle_service)
        self.control_layout.addWidget(self.toggle_button)
        
        # Set the initial state of the toggle based on whether the monitor is running
        if self.file_monitor and self.file_monitor.is_running():
            self.toggle_button.setChecked(True)
        
        # Appearance mode
        self.appearance_mode = QComboBox()
        self.appearance_mode.addItems(["System", "Light", "Dark"])
        self.appearance_mode.currentTextChanged.connect(self.change_appearance_mode)
        self.control_layout.addWidget(self.appearance_mode)
        
        self.sidebar_layout.addWidget(self.control_frame)
        self.main_layout.addWidget(self.sidebar_frame)
                     
    def create_main_content(self):
        """Create the main content area"""
        # Main frame with vertical layout to hold content and status bar
        self.main_area = QFrame()
        self.main_area_layout = QVBoxLayout(self.main_area)
        self.main_area_layout.setContentsMargins(0, 0, 0, 0)
        self.main_area_layout.setSpacing(0)
        
        # Main content frame that will hold the stacked widgets
        self.main_frame = QStackedWidget()
        self.main_area_layout.addWidget(self.main_frame)
        
        # Status bar at the bottom
        self.create_status_bar()
        self.main_area_layout.addWidget(self.status_bar)
        
        # Add the main area to the main layout
        self.main_layout.addWidget(self.main_area)
        
        # Create all content frames
        self.create_dashboard_frame()
        self.create_statistics_frame()
        self.create_settings_frame()
        
        # Start with dashboard
        self.show_dashboard()
        
    def create_dashboard_frame(self):
        """Create the dashboard content"""
        self.dashboard_frame = QWidget()
        dashboard_layout = QVBoxLayout(self.dashboard_frame)
        self.main_frame.addWidget(self.dashboard_frame)
        
        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        
        header_label = QLabel("Dashboard")
        header_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        sort_now_btn = QPushButton("Sort Now")
        sort_now_btn.clicked.connect(self.sort_now)
        header_layout.addWidget(sort_now_btn)
        
        dashboard_layout.addWidget(header)
        
        # Activity section
        activity_frame = QFrame()
        activity_layout = QVBoxLayout(activity_frame)
        
        activity_header = QFrame()
        activity_header_layout = QHBoxLayout(activity_header)
        
        activity_label = QLabel("Recent Activity")
        activity_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        activity_header_layout.addWidget(activity_label)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_dashboard)
        activity_header_layout.addWidget(refresh_btn)
        
        activity_layout.addWidget(activity_header)
        
        # Recent activity list (scrollable)
        self.activity_list = QScrollArea()
        self.activity_list.setWidgetResizable(True)
        self.activity_list_content = QWidget()
        self.activity_list_layout = QVBoxLayout(self.activity_list_content)
        self.activity_list.setWidget(self.activity_list_content)
        
        activity_layout.addWidget(self.activity_list)
        dashboard_layout.addWidget(activity_frame)
        
        # Summary cards
        summary_frame = QFrame()
        summary_layout = QGridLayout(summary_frame)
        
        # Create stat cards (will populate in refresh_dashboard)
        self.files_sorted_card = self.create_stat_card(summary_frame, "Files Sorted", "0", 0)
        self.space_saved_card = self.create_stat_card(summary_frame, "Space Saved", "0 B", 1)
        self.categories_card = self.create_stat_card(summary_frame, "Categories", str(len(self.config.get("categories", {}))), 2)
        
        summary_layout.addWidget(self.files_sorted_card, 0, 0)
        summary_layout.addWidget(self.space_saved_card, 0, 1)
        summary_layout.addWidget(self.categories_card, 0, 2)
        
        dashboard_layout.addWidget(summary_frame)
        
        # Initial refresh to populate with real data
        self.refresh_dashboard()
        
    def create_statistics_frame(self):
        """Create the statistics content"""
        self.statistics_frame = QWidget()
        stats_layout = QVBoxLayout(self.statistics_frame)
        self.main_frame.addWidget(self.statistics_frame)
        
        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        
        header_label = QLabel("Statistics")
        header_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        self.time_range_selector = QComboBox()
        self.time_range_selector.addItems(["Week", "Month", "Year"])
        self.time_range_selector.setCurrentText("Month")
        self.time_range_selector.currentTextChanged.connect(self.change_time_range)
        header_layout.addWidget(self.time_range_selector)
        
        stats_layout.addWidget(header)
        
        # Use vertical layout instead of split screen
        charts_container = QFrame()
        charts_layout = QVBoxLayout(charts_container)
        
        # Pie chart section
        self.pie_frame = QFrame()
        self.pie_layout = QVBoxLayout(self.pie_frame)
        
        pie_header = QLabel("Files by Category")
        pie_header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.pie_layout.addWidget(pie_header)
        
        self.pie_chart_frame = QFrame()
        pie_chart_layout = QVBoxLayout(self.pie_chart_frame)
        self.pie_layout.addWidget(self.pie_chart_frame)
        
        charts_layout.addWidget(self.pie_frame)
        
        # Bar chart section
        self.bar_frame = QFrame()
        self.bar_layout = QVBoxLayout(self.bar_frame)
        
        bar_header = QLabel("Files Sorted by Month")
        bar_header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.bar_layout.addWidget(bar_header)
        
        self.bar_chart_frame = QFrame()
        bar_chart_layout = QVBoxLayout(self.bar_chart_frame)
        self.bar_layout.addWidget(self.bar_chart_frame)
        
        charts_layout.addWidget(self.bar_frame)
        
        stats_layout.addWidget(charts_container)
        
        # Initial refresh to populate with real data
        self.refresh_statistics()
        
    def create_settings_frame(self):
        """Create the settings content"""
        self.settings_frame = QWidget()
        settings_main_layout = QVBoxLayout(self.settings_frame)
        self.main_frame.addWidget(self.settings_frame)
        
        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        
        header_label = QLabel("Settings")
        header_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        header_layout.addWidget(save_btn)
        
        settings_main_layout.addWidget(header)
        
        # Settings content in a scrollable frame
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_content = QWidget()
        settings_layout = QVBoxLayout(settings_content)
        settings_scroll.setWidget(settings_content)
        
        # Folder settings section
        folder_section = QFrame()
        folder_layout = QVBoxLayout(folder_section)
        
        folder_label = QLabel("Folder Settings")
        folder_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        folder_layout.addWidget(folder_label)
        
        # Source folder
        source_frame = QFrame()
        source_layout = QHBoxLayout(source_frame)
        
        source_label = QLabel("Source Folder:")
        source_layout.addWidget(source_label)
        
        self.source_entry = QLineEdit()
        self.source_entry.setText(self.config.get("source_folder", str(Path.home() / "Downloads")))
        source_layout.addWidget(self.source_entry)
        
        source_btn = QPushButton("Browse")
        source_btn.setIcon(self.folder_icon)
        source_btn.clicked.connect(self.browse_source)
        source_layout.addWidget(source_btn)
        
        folder_layout.addWidget(source_frame)
        
        # Destination folder
        dest_frame = QFrame()
        dest_layout = QHBoxLayout(dest_frame)
        
        dest_label = QLabel("Destination:")
        dest_layout.addWidget(dest_label)
        
        self.dest_entry = QLineEdit()
        self.dest_entry.setText(self.config.get("destination_folder", str(Path.home() / "Downloads")))
        dest_layout.addWidget(self.dest_entry)
        
        dest_btn = QPushButton("Browse")
        dest_btn.setIcon(self.folder_icon)
        dest_btn.clicked.connect(self.browse_destination)
        dest_layout.addWidget(dest_btn)
        
        folder_layout.addWidget(dest_frame)
        
        settings_layout.addWidget(folder_section)
        
        # Behavior section
        behavior_section = QFrame()
        behavior_layout = QVBoxLayout(behavior_section)
        
        behavior_label = QLabel("Behavior")
        behavior_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        behavior_layout.addWidget(behavior_label)
        
        options_frame = QFrame()
        options_layout = QHBoxLayout(options_frame)
        
        self.startup_var = QCheckBox("Run at Windows startup")
        self.startup_var.setChecked(self.config.get("run_at_startup", True))
        options_layout.addWidget(self.startup_var)
        
        self.notify_var = QCheckBox("Show notifications")
        self.notify_var.setChecked(self.config.get("show_notifications", True))
        options_layout.addWidget(self.notify_var)
        
        behavior_layout.addWidget(options_frame)
        
        # Scan schedule section
        schedule_frame = QFrame()
        schedule_layout = QVBoxLayout(schedule_frame)
        
        schedule_label = QLabel("Folder Scan Schedule:")
        schedule_label.setFont(QFont("Arial", QFont.Weight.Bold))
        schedule_layout.addWidget(schedule_label)
        
        # Scan mode options
        scan_options_frame = QFrame()
        scan_options_layout = QHBoxLayout(scan_options_frame)
        
        self.scan_mode_var = QRadioButton("Regular monitoring")
        self.scan_mode_var.setChecked(self.config.get("scan_mode", "regular") == "regular")
        self.scan_mode_var.toggled.connect(self.toggle_schedule_options)
        scan_options_layout.addWidget(self.scan_mode_var)
        
        self.scheduled_rb = QRadioButton("Scheduled scans")
        self.scheduled_rb.setChecked(self.config.get("scan_mode", "regular") == "scheduled")
        self.scheduled_rb.toggled.connect(self.toggle_schedule_options)
        scan_options_layout.addWidget(self.scheduled_rb)
        
        schedule_layout.addWidget(scan_options_frame)
        
        # Schedule times container (initially hidden if in regular mode)
        self.schedule_times_frame = QFrame()
        self.schedule_times_layout = QVBoxLayout(self.schedule_times_frame)
        
        # Time slots management
        time_header_frame = QFrame()
        time_header_layout = QHBoxLayout(time_header_frame)
        
        time_label = QLabel("Scheduled Scan Times:")
        time_header_layout.addWidget(time_label)
        
        add_time_btn = QPushButton("Add Time")
        add_time_btn.clicked.connect(self.add_scheduled_time)
        time_header_layout.addWidget(add_time_btn)
        
        self.schedule_times_layout.addWidget(time_header_frame)
        
        # Container for time slots
        self.time_slots_frame = QScrollArea()
        self.time_slots_frame.setWidgetResizable(True)
        self.time_slots_content = QWidget()
        self.time_slots_layout = QVBoxLayout(self.time_slots_content)
        self.time_slots_frame.setWidget(self.time_slots_content)
        
        self.schedule_times_layout.addWidget(self.time_slots_frame)
        
        # Offline recovery option
        self.offline_recovery_var = QCheckBox("Perform scan when computer comes back online if a scheduled scan was missed")
        self.offline_recovery_var.setChecked(self.config.get("scan_when_back_online", True))
        self.schedule_times_layout.addWidget(self.offline_recovery_var)
        
        schedule_layout.addWidget(self.schedule_times_frame)
        behavior_layout.addWidget(schedule_frame)
        
        settings_layout.addWidget(behavior_section)
        
        # Initialize the schedule UI based on current mode
        self.toggle_schedule_options()
        self.load_scheduled_times()
        
        # Categories section
        categories_section = QFrame()
        categories_layout = QVBoxLayout(categories_section)
        
        cats_header = QFrame()
        cats_header_layout = QHBoxLayout(cats_header)
        
        cats_label = QLabel("Categories")
        cats_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        cats_header_layout.addWidget(cats_label)
                   
        add_cat_btn = QPushButton("Add Category")
        add_cat_btn.clicked.connect(self.add_category)
        cats_header_layout.addWidget(add_cat_btn)
        
        categories_layout.addWidget(cats_header)
        
        # Category list
        self.cat_list_frame = QFrame()
        self.cat_list_layout = QVBoxLayout(self.cat_list_frame)
        
        categories_layout.addWidget(self.cat_list_frame)
        settings_layout.addWidget(categories_section)
        
        settings_main_layout.addWidget(settings_scroll)
        
        # Populate categories from config
        self.refresh_categories()

    def create_status_bar(self):
        """Create status bar at bottom of window"""
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(25)
        
        self.status_layout = QHBoxLayout(self.status_bar)
        self.status_layout.setContentsMargins(10, 0, 10, 0)
        
        self.status_label = QLabel("Ready | Last sort: Never")
        self.status_layout.addWidget(self.status_label)
        
        self.status_layout.addStretch()
        
        self.version_label = QLabel("v1.0.0")
        self.status_layout.addWidget(self.version_label)
        
        self.main_layout.addWidget(self.status_bar)

    def refresh_categories(self):
        """Refresh the categories list in settings"""
        # Clear existing categories
        for i in reversed(range(self.cat_list_layout.count())):
            widget = self.cat_list_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
            
        # Add categories from config
        for i, (cat_name, extensions) in enumerate(self.config.get("categories", {}).items()):
            self.create_category_item(self.cat_list_frame, cat_name, ", ".join(extensions), i)

    # Helper methods for UI components
    def create_stat_card(self, parent, title, value, column):
        """Create a statistics card in the dashboard"""
        card = QFrame(parent)
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setFrameShadow(QFrame.Shadow.Raised)
        card.setProperty("class", "card")  # Apply card styling
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title, card)
        title_label.setProperty("title", "true")  # Set title property for styling
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value, card)
        value_label.setProperty("value", "true")  # Set value property for styling
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)
        
        return value_label
    
    def add_activity_item(self, parent, filename, category, time_ago):
        """Add an activity item to the list"""
        item = QFrame()
        item.setFrameShape(QFrame.Shape.StyledPanel)
        item.setProperty("class", "activity-item")  # Apply activity-item styling
        item_layout = QVBoxLayout(item)
        
        # File info
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        
        filename_label = QLabel(filename)
        filename_label.setProperty("filename", "true")  # Set filename property for styling
        info_layout.addWidget(filename_label)
        
        details_frame = QFrame()
        details_layout = QHBoxLayout(details_frame)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        category_label = QLabel(category)
        category_label.setProperty("details", "true")  # Set details property for styling
        details_layout.addWidget(category_label)
                   
        separator_label = QLabel(" • ")
        separator_label.setProperty("details", "true")  # Set details property for styling
        details_layout.addWidget(separator_label)
                   
        time_ago_label = QLabel(time_ago)
        time_ago_label.setProperty("details", "true")  # Set details property for styling
        details_layout.addWidget(time_ago_label)
        
        details_layout.addStretch()
        
        info_layout.addWidget(details_frame)
        item_layout.addWidget(info_frame)
        self.activity_list_layout.addWidget(item)
    
    def create_category_item(self, parent, name, extensions, row):
        """Create a category item in settings"""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setProperty("class", "category-item")  # Apply category-item styling
        frame_layout = QHBoxLayout(frame)
        
        # Category name
        name_label = QLabel(name)
        name_label.setFont(QFont("Arial", QFont.Weight.Bold))
        frame_layout.addWidget(name_label)
        
        # Extensions list        
        extensions_label = QLabel(extensions)
        frame_layout.addWidget(extensions_label)
        
        frame_layout.addStretch()
        
        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("secondary", "true")  # Apply secondary button styling
        edit_btn.clicked.connect(lambda checked, n=name: self.edit_category(n))
        frame_layout.addWidget(edit_btn)
        
        self.cat_list_layout.addWidget(frame)
        
    # UI navigation and action methods
    def show_dashboard(self):
        # Show dashboard
        self.main_frame.setCurrentWidget(self.dashboard_frame)
        
        # Update active button
        self.nav_dashboard.setStyleSheet("background-color: lightgray;")
        self.nav_stats.setStyleSheet("")
        self.nav_settings.setStyleSheet("")
        
    def show_statistics(self):
        # Show statistics
        self.main_frame.setCurrentWidget(self.statistics_frame)
        
        # Update active button
        self.nav_dashboard.setStyleSheet("")
        self.nav_stats.setStyleSheet("background-color: lightgray;")
        self.nav_settings.setStyleSheet("")
        
    def show_settings(self):
        # Show settings
        self.main_frame.setCurrentWidget(self.settings_frame)
        
        # Update active button
        self.nav_dashboard.setStyleSheet("")
        self.nav_stats.setStyleSheet("")
        self.nav_settings.setStyleSheet("background-color: lightgray;")
    
    # Action handlers
    def toggle_service(self):
        """Toggle the background service on/off"""
        if not self.file_monitor:
            return
            
        state = "Active" if self.toggle_button.isChecked() else "Paused"
        
        if state == "Active" and not self.file_monitor.is_running():
            self.file_monitor.start()
        elif state == "Paused" and self.file_monitor.is_running():
            self.file_monitor.stop()
            
        self.status_label.setText(f"{state} | Last sort: {datetime.now().strftime('%H:%M:%S')}")
    
    def sort_now(self):
        """Manually trigger sorting"""
        source_folder = self.config.get("source_folder", str(Path.home() / "Downloads"))
        if Path(source_folder).exists():
            success_count, error_count = self.sorter.sort_directory(source_folder)
            current_time = datetime.now().strftime('%H:%M:%S')
            self.status_label.setText(f"Active | Last sort: {current_time} | {success_count} files sorted")
    
    def save_settings(self):
        """Save application settings"""
        # Update config with values from UI
        self.config["source_folder"] = self.source_entry.text()
        self.config["destination_folder"] = self.dest_entry.text()
        self.config["run_at_startup"] = self.startup_var.isChecked()
        self.config["show_notifications"] = self.notify_var.isChecked()
        
        # Save scan schedule settings
        self.config["scan_mode"] = "scheduled" if self.scheduled_rb.isChecked() else "regular"
        self.config["scan_when_back_online"] = self.offline_recovery_var.isChecked()
        
        # Save config
        from sorter.utils import save_config, set_run_at_startup
        save_config(self.config)
        set_run_at_startup(self.config["run_at_startup"])
        
        # Restart file monitor with new settings if it's running
        if self.file_monitor and self.file_monitor.is_running():
            self.file_monitor.stop()
            self.file_monitor.start()
            
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully.")
    
    def browse_source(self):
        """Browse for source folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_entry.setText(folder)
    
    def browse_destination(self):
        """Browse for destination folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_entry.setText(folder)
    
    def add_category(self):
        """Add a new category"""
        # Would open add category dialog in real implementation
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "Add Category", "Enter category name:")
        if ok and name and name not in self.config.get("categories", {}):
            extensions, ok = QInputDialog.getText(self, "Add Category", "Enter file extensions (comma separated):")
            if ok and extensions:
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
        from PyQt6.QtWidgets import QInputDialog
        
        if category_name in self.config.get("categories", {}):
            current_extensions = ", ".join(self.config["categories"][category_name])
            new_extensions, ok = QInputDialog.getText(self, "Edit Category", 
                                                 f"Edit extensions for {category_name}:", 
                                                 text=current_extensions)
            
            if ok and new_extensions is not None:  # Cancel returns None
                ext_list = [x.strip() for x in new_extensions.split(",")]
                ext_list = [x if x.startswith(".") else f".{x}" for x in ext_list]
                
                # Update config
                self.config["categories"][category_name] = ext_list
                
                # Refresh the UI
                self.refresh_categories()
    
    def change_appearance_mode(self, new_appearance_mode):
        """Change the app appearance mode"""
        # Save the setting for persistence across app restarts
        self.config["appearance_mode"] = new_appearance_mode.lower()
        save_config(self.config)
        
        if new_appearance_mode.lower() == "dark":
            # Set dark palette
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            QApplication.setPalette(palette)
        elif new_appearance_mode.lower() == "light":
            # Reset to the light palette
            QApplication.setPalette(QApplication.style().standardPalette())
        else:  # System default
            # Try to detect system theme if possible, otherwise use light
            try:
                import darkdetect
                if darkdetect.isDark():
                    # Same dark palette as above
                    palette = QPalette()
                    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
                    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
                    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
                    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
                    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
                    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
                    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
                    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
                    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
                    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
                    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
                    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
                    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
                    QApplication.setPalette(palette)
                else:
                    QApplication.setPalette(QApplication.style().standardPalette())
            except ImportError:
                # If darkdetect is not available, default to light theme
                QApplication.setPalette(QApplication.style().standardPalette())
    
    # Dashboard and statistics methods
    def refresh_dashboard(self):
        """Refresh the dashboard with current statistics"""
        # Clear activity list
        for i in reversed(range(self.activity_list_layout.count())):
            widget = self.activity_list_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
            
        # Get recent activity data
        recent_activity = self.stats.get_recent_activity(limit=10)
        
        if (recent_activity):
            for activity in recent_activity:
                self.add_activity_item(
                    self.activity_list_content,
                    activity['filename'],
                    activity['category'],
                    activity['time_ago']
                )
        else:
            # Show placeholder message when no activity
            placeholder = QFrame()
            placeholder_layout = QVBoxLayout(placeholder)
            
            placeholder_label = QLabel("No recent activity")
            placeholder_label.setFont(QFont("Arial", 14))
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_layout.addWidget(placeholder_label)
            
            self.activity_list_layout.addWidget(placeholder)
        
        # Update summary statistics
        total_stats = self.stats.get_total_stats()
        
        self.files_sorted_card.setText(str(total_stats['total_files']))
        self.space_saved_card.setText(total_stats['total_size'])
        self.categories_card.setText(str(total_stats['category_count'] or len(self.config.get("categories", {}))))
    
    def refresh_statistics(self):
        """Refresh statistical visualizations"""
        # Clear existing charts from the frames
        for i in reversed(range(self.pie_chart_frame.layout().count())):
            item = self.pie_chart_frame.layout().itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        for i in reversed(range(self.bar_chart_frame.layout().count())):
            item = self.bar_chart_frame.layout().itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            
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
        # Create a pie series
        series = QPieSeries()
        
        # Get total count
        total_count = sum(item['count'] for item in data)
        if total_count == 0:
            self.show_no_data_message(parent, "No files sorted yet")
            return
        
        # Define colors for pie slices
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#7f8c8d']
        
        # Limit to top 7 categories for visualization
        display_data = data[:7] if len(data) > 7 else data
        
        for i, item in enumerate(display_data):
            percentage = item['count'] / total_count
            slice = series.append(item['category'], item['count'])
            slice.setBrush(QColor(colors[i % len(colors)]))
        
        # Create chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Files by Category")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Add chart view to layout
        parent.layout().addWidget(chart_view)
    
    def draw_bar_chart(self, parent, data):
        """Draw a bar chart showing files sorted by month"""
        # Skip if no data
        if not data or not any(month['categories'] for month in data):
            self.show_no_data_message(parent, "No monthly data available")
            return
        
        # Define colors for categories
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e']
        
        # Create bar series
        series = QBarSeries()
        
        # Get all categories across all months
        all_categories = set()
        for month in data:
            all_categories.update(month['categories'].keys())
            
        # Filter to top 5 categories for visualization
        categories = list(all_categories)[:5]
        
        # Create bar sets for each category
        bar_sets = {}
        for category in categories:
            bar_set = QBarSet(category)
            bar_sets[category] = bar_set
        
        # Add data to bar sets
        for month in data:
            for category in categories:
                value = month['categories'].get(category, 0)
                bar_sets[category].append(value)
        
        # Add bar sets to series
        for i, (category, bar_set) in enumerate(bar_sets.items()):
            bar_set.setColor(QColor(colors[i % len(colors)]))
            series.append(bar_set)
        
        # Create chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Files Sorted by Month")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # Create axis
        axis_x = QBarCategoryAxis()
        axis_x.append([month['month'] for month in data])
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        max_value = 1  # Default minimum to avoid division by zero
        for bar_set in bar_sets.values():
            if len(bar_set) > 0:
                max_value = max(max_value, max(bar_set))
        axis_y.setRange(0, max_value)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Add chart view to layout
        parent.layout().addWidget(chart_view)
    
    def show_no_data_message(self, parent, message):
        """Show a message when no data is available for charts"""
        label = QLabel(message)
        label.setFont(QFont("Arial", 14))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        parent.layout().addWidget(label)
    
    def change_time_range(self, value):
        """Change the time range for statistics"""
        self.current_time_range = value.lower()
        self.refresh_statistics()
    
    def toggle_schedule_options(self):
        """Show or hide schedule options based on selected scan mode"""
        if self.scheduled_rb.isChecked():
            self.schedule_times_frame.show()
        else:
            self.schedule_times_frame.hide()
            
    def add_scheduled_time(self):
        """Add a new scheduled scan time"""
        from PyQt6.QtWidgets import QInputDialog
        
        # Show time picker dialog
        time_str, ok = QInputDialog.getText(self, "Add Scheduled Time", 
                                        "Enter time (24-hour format, HH:MM):",
                                        text="12:00")
        
        if ok and time_str:
            try:
                # Validate time format
                hour, minute = map(int, time_str.split(':'))
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    QMessageBox.critical(self, "Invalid Time", "Please enter a valid time in 24-hour format (HH:MM)")
                    return
                    
                # Format time properly
                formatted_time = f"{hour:02d}:{minute:02d}"
                
                # Add to config if not already exists
                if "scheduled_times" not in self.config:
                    self.config["scheduled_times"] = []
                
                if formatted_time not in self.config["scheduled_times"]:
                    self.config["scheduled_times"].append(formatted_time)
                    self.refresh_time_slots()
            except ValueError:
                QMessageBox.critical(self, "Invalid Format", "Please enter time in HH:MM format")
    
    def load_scheduled_times(self):
        """Load scheduled times from config"""
        self.refresh_time_slots()
    
    def refresh_time_slots(self):
        """Refresh the time slots UI"""
        # Clear existing time slots
        for i in reversed(range(self.time_slots_layout.count())):
            widget = self.time_slots_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        # Add time slots from config
        scheduled_times = sorted(self.config.get("scheduled_times", []))
        
        if not scheduled_times:
            # Show placeholder when no times are scheduled
            placeholder_label = QLabel("No scheduled times set")
            placeholder_label.setFont(QFont("Arial", 14))
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.time_slots_layout.addWidget(placeholder_label)
        else:
            for time_str in scheduled_times:
                self.create_time_slot_item(time_str)
    
    def create_time_slot_item(self, time_str):
        """Create a time slot item in UI"""
        slot_frame = QFrame()
        slot_frame.setFrameShape(QFrame.Shape.StyledPanel)
        slot_layout = QHBoxLayout(slot_frame)
        
        # Time display
        time_label = QLabel(time_str)
        time_label.setFont(QFont("Arial", QFont.Weight.Bold))
        slot_layout.addWidget(time_label)
        
        slot_layout.addStretch()
        
        # Delete button
        delete_btn = QPushButton("×")
        delete_btn.clicked.connect(lambda checked=False, t=time_str: self.remove_scheduled_time(t))
        slot_layout.addWidget(delete_btn)
        
        self.time_slots_layout.addWidget(slot_frame)
    
    def remove_scheduled_time(self, time_str):
        """Remove a scheduled time"""
        if "scheduled_times" in self.config and time_str in self.config["scheduled_times"]:
            self.config["scheduled_times"].remove(time_str)
            self.refresh_time_slots()
            
    def apply_stylesheet(self):
        """Load and apply the application stylesheet"""
        stylesheet_path = Path(__file__).parent / "resources" / "style.qss"
        if stylesheet_path.exists():
            try:
                with open(stylesheet_path, 'r') as f:
                    self.setStyleSheet(f.read())
            except Exception as e:
                print(f"Error loading stylesheet: {e}")
                
        # Set object names for CSS selectors
        self.sidebar_frame.setObjectName("sidebar")
        self.logo_label.setObjectName("logo")
        self.status_bar.setObjectName("statusBar")