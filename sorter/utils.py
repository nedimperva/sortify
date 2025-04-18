"""
Utility functions for the Downloads Sorter application.
"""
import os
import json
import logging
from pathlib import Path

def setup_logging():
    """Configure logging for the application"""
    log_file = Path.home() / ".sortify" / "downloads_sorter.log"
    
    # Create log directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file)),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("sortify")

def get_config_path():
    """Get the path to the configuration file"""
    config_dir = Path.home() / ".sortify"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    return config_dir / "config.json"

def load_config():
    """Load configuration from the config file"""
    config_path = get_config_path()
    
    # Create default config if it doesn't exist
    if not config_path.exists():
        create_default_config()
        
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        # Return default config if loading fails
        return create_default_config()

def save_config(config):
    """Save configuration to the config file"""
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving config: {e}")
        return False

def create_default_config():
    """Create and return default configuration"""
    downloads_path = str(Path.home() / "Downloads")
    
    default_config = {
        "source_folder": downloads_path,
        "destination_folder": downloads_path,
        "run_at_startup": True,
        "categories": {
            "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".doc", ".ppt", ".pptx", ".odt", ".ods", ".rtf", ".csv"],
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".bmp", ".tiff", ".webp"],
            "Videos": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"],
            "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "Programs": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"],
            "Others": []
        },
        "exclusions": ["partial", ".crdownload", ".part", ".tmp"],
        "min_file_size": 1024,  # 1KB
        "sort_delay": 5,  # 5 seconds
        "show_notifications": True
    }
    
    # Save the default configuration
    config_path = get_config_path()
    try:
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
    except Exception as e:
        logging.error(f"Error creating default config: {e}")
        
    return default_config

def is_running_at_startup():
    """Check if the app is configured to run at Windows startup"""
    import winreg
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        
        try:
            value, _ = winreg.QueryValueEx(key, "SortifyDownloadSorter")
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False

def set_run_at_startup(enable=True):
    """Configure the application to run at Windows startup"""
    import winreg
    import sys
    
    run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "SortifyDownloadSorter"
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            run_key,
            0, winreg.KEY_WRITE
        )
        
        if enable:
            app_path = sys.executable
            if app_path.endswith("python.exe"):
                # If running from Python interpreter, use the script path
                script_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}" "{script_path}"')
            else:
                # If running from executable
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
                
        winreg.CloseKey(key)
        return True
    except Exception as e:
        logging.error(f"Error setting startup: {e}")
        return False