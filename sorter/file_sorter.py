"""
File sorter module for Downloads Sorter application.
Handles the categorization and sorting of files based on their type.
"""
import os
import logging
import shutil
from pathlib import Path
from datetime import datetime
from .utils import load_config
from .stats import SortingStats

class FileSorter:
    """
    Sorts files into categories based on file extension.
    Organizes files into year/month/category folders.
    """
    def __init__(self):
        self.logger = logging.getLogger("FileSorter")
        self.config = load_config()
        self.stats = SortingStats()
        
    def get_category(self, file_path):
        """Determine the category of a file based on its extension"""
        extension = file_path.suffix.lower()
        
        # Check each category for the extension
        for category, extensions in self.config.get("categories", {}).items():
            if extension in extensions:
                return category
                
        # Return Others if no category matches
        return "Others"
    
    def get_target_directory(self, file_path):
        """Create the target directory path based on date and category"""
        creation_date = datetime.fromtimestamp(file_path.stat().st_ctime)
        category = self.get_category(file_path)
        
        # Build path: destination/year/month/category
        destination = Path(self.config.get("destination_folder", 
                                         str(Path.home() / "Downloads")))
        
        year_folder = str(creation_date.year)
        month_folder = creation_date.strftime("%m - %B")
        
        target_dir = destination / year_folder / month_folder / category
        
        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
        
        return target_dir, category
        
    def sort_file(self, file_path):
        """Sort a file into the appropriate directory"""
        if not file_path.exists():
            self.logger.warning(f"File no longer exists: {file_path}")
            return False
            
        try:
            target_dir, category = self.get_target_directory(file_path)
            target_path = target_dir / file_path.name
            
            # Handle file conflicts (if target file already exists)
            if target_path.exists():
                base_name = target_path.stem
                extension = target_path.suffix
                counter = 1
                
                # Try adding a counter until we find an available filename
                while target_path.exists():
                    new_name = f"{base_name}_{counter}{extension}"
                    target_path = target_dir / new_name
                    counter += 1
            
            # Move the file
            shutil.move(str(file_path), str(target_path))
            self.logger.info(f"Moved file: {file_path} -> {target_path}")
            
            # Record statistics
            self.stats.record_sorted_file(file_path, category, target_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sorting file {file_path}: {e}")
            return False
            
    def sort_directory(self, directory_path):
        """Sort all files in a directory (one-time bulk sort)"""
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            self.logger.error(f"Invalid directory: {directory_path}")
            return False
            
        success_count = 0
        error_count = 0
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                try:
                    if self.sort_file(file_path):
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    self.logger.error(f"Error sorting {file_path}: {e}")
                    error_count += 1
                    
        self.logger.info(f"Bulk sort complete. Success: {success_count}, Errors: {error_count}")
        return success_count, error_count