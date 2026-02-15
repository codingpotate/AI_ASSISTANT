import os
import shutil
from pathlib import Path
import time
from datetime import datetime
from assistant.plugin_base import AssistantPlugin

class FileOrganizerPlugin(AssistantPlugin):
    def get_name(self):
        return "organize_files"
    
    def get_description(self):
        return "Organize files in a directory by their file type"
    
    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Path to the directory to organize"
                },
                "organize_by": {
                    "type": "string",
                    "enum": ["type", "date", "size"],
                    "description": "How to organize files"
                }
            },
            "required": ["directory"]
        }
    
    def execute(self, directory: str, organize_by: str = "type"):
        try:
            path = Path(directory).expanduser().resolve()
            
            if not path.exists():
                return f"Error: Directory '{directory}' does not exist."
            
            if not path.is_dir():
                return f"Error: '{directory}' is not a directory."
            
            # Get list of files (not directories)
            files = [f for f in path.iterdir() if f.is_file()]
            
            if not files:
                return f"No files found in '{directory}' to organize."
            
            if organize_by == "type":
                return self._organize_by_type(path, files)
            elif organize_by == "date":
                return self._organize_by_date(path, files)
            elif organize_by == "size":
                return self._organize_by_size(path, files)
            else:
                return f"Unknown organization method: {organize_by}"
                
        except PermissionError:
            return f"Error: Permission denied for directory '{directory}'."
        except Exception as e:
            return f"Error organizing files: {str(e)}"
    
    def _organize_by_type(self, path: Path, files: list):
        """Organize files by their extension"""
        file_types = {
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'],
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff', '.psd'],
            'Videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v', '.mpg'],
            'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.json', '.xml'],
            'Executables': ['.exe', '.msi', '.bat', '.sh', '.app', '.dmg'],
            'Data': ['.csv', '.tsv', '.sql', '.db', '.sqlite', '.jsonl']
        }
        
        moved_count = 0
        skipped_count = 0
        created_folders = []
        
        for file in files:
            file_extension = file.suffix.lower()
            file_moved = False
            
            for category, extensions in file_types.items():
                if file_extension in extensions:
                    # Create category folder if it doesn't exist
                    category_folder = path / category
                    if not category_folder.exists():
                        category_folder.mkdir()
                        created_folders.append(category)
                    
                    # Check if file already exists in target
                    target_path = category_folder / file.name
                    if target_path.exists():
                        # Add timestamp to avoid overwrite
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_name = f"{file.stem}_{timestamp}{file.suffix}"
                        target_path = category_folder / new_name
                    
                    # Move file
                    try:
                        shutil.move(str(file), str(target_path))
                        moved_count += 1
                        file_moved = True
                        break
                    except Exception as e:
                        return f"Error moving file {file.name}: {str(e)}"
            
            if not file_moved:
                # Move to "Other" folder for unknown types
                other_folder = path / "Other"
                if not other_folder.exists():
                    other_folder.mkdir()
                    if "Other" not in created_folders:
                        created_folders.append("Other")
                
                target_path = other_folder / file.name
                if target_path.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_name = f"{file.stem}_{timestamp}{file.suffix}"
                    target_path = other_folder / new_name
                
                try:
                    shutil.move(str(file), str(target_path))
                    moved_count += 1
                except Exception as e:
                    skipped_count += 1
        
        result = f"Organized files in '{path.name}':\n"
        result += f"• Total files processed: {len(files)}\n"
        result += f"• Files moved: {moved_count}\n"
        result += f"• Files skipped: {skipped_count}\n"
        
        if created_folders:
            result += f"• Created folders: {', '.join(sorted(set(created_folders)))}\n"
        
        result += f"\nOrganization complete. Check the '{path.name}' directory for the new folders."
        return result
    
    def _organize_by_date(self, path: Path, files: list):
        """Organize files by creation date"""
        # Implementation for date-based organization
        return "Date-based organization is not yet implemented. Use 'type' instead."
    
    def _organize_by_size(self, path: Path, files: list):
        """Organize files by size"""
        # Implementation for size-based organization
        return "Size-based organization is not yet implemented. Use 'type' instead."