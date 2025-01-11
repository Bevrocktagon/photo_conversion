import os
import shutil
from PIL import Image
import pillow_heif
import piexif
from datetime import datetime

# Register the HEIC opener for Pillow
pillow_heif.register_heif_opener()

def format_timestamp(timestamp):
    """Format timestamp to ensure it is exactly 16 characters long."""
    return timestamp[:16].ljust(16, '0')

def get_jpg_exif_creation_time(jpg_path):
    """Get the original creation time from EXIF metadata in the JPG file."""
    try:
        with Image.open(jpg_path) as img:
            exif_data = img._getexif()
            if exif_data:
                # Extract the DateTimeOriginal tag (36867 / 0x9003)
                date_str = exif_data.get(36867)
                subsec_str = exif_data.get(37520)
                
                if date_str:
                    # Convert bytes to string and format to YYYYMMDDHHMMSS
                    datetime_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    
                    if subsec_str:
                        # Append hundredths of seconds if available
                        formatted_time = datetime_obj.strftime('%Y%m%d%H%M%S') + f"{int(subsec_str):02}"
                    else:
                        formatted_time = datetime_obj.strftime('%Y%m%d%H%M%S')
                    
                    return format_timestamp(formatted_time)
        return None
    except Exception as e:
        print(f"Error getting EXIF data from {jpg_path}: {e}")
        return None

def get_file_creation_time(file_path):
    """Get file modification time as a fallback if EXIF metadata is not available."""
    try:
        creation_time = os.path.getmtime(file_path)
        datetime_obj = datetime.fromtimestamp(creation_time)
        # Extract hundredths of seconds from the float timestamp
        formatted_time = datetime_obj.strftime('%Y%m%d%H%M%S') + f"{int(datetime_obj.microsecond / 10000):02}"
        return format_timestamp(formatted_time)
    except Exception as e:
        print(f"Error getting file modification time for {file_path}: {e}")
        return None

def rename_jpg_files(directory):
    """Rename all JPG files in the specified directory based on their EXIF data or file modification time."""
    for filename in os.listdir(directory):
        if filename.lower().endswith(".jpg"):
            file_path = os.path.join(directory, filename)

            # Try to get the creation time from EXIF data
            formatted_time = get_jpg_exif_creation_time(file_path)
            if not formatted_time:  # Fallback to file creation time if EXIF data is missing
                formatted_time = get_file_creation_time(file_path)
            
            if formatted_time:
                # Rename the file
                new_filename = f"{formatted_time}.jpg"
                new_file_path = os.path.join(directory, new_filename)
                shutil.move(file_path, new_file_path)
                print(f"Renamed {file_path} to {new_file_path}")
            else:
                print(f"Skipping {file_path}: unable to retrieve creation time")

# Set the directory containing JPG files
jpg_directory = '/Volumes/disc0/ItalyPhotos/BigCamera/'

# Rename JPG files in the specified directory
rename_jpg_files(jpg_directory)
