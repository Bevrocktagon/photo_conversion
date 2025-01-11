import os
import shutil
from PIL import Image
import pillow_heif
import piexif
from concurrent.futures import ThreadPoolExecutor, as_completed
from moviepy.editor import VideoFileClip
from datetime import datetime
import subprocess

# Register the HEIC opener for Pillow
pillow_heif.register_heif_opener()

def format_timestamp(timestamp):
    """Format timestamp to ensure it is exactly 16 characters long."""
    # Truncate or pad the timestamp to ensure it is 16 characters
    return timestamp[:16].ljust(16, '0')

def get_heic_exif_creation_time(heic_path):
    """Get the original creation time from EXIF metadata in the HEIC file."""
    try:
        # Open the HEIC file using pillow_heif
        heif_file = pillow_heif.open_heif(heic_path)
        
        # Extract the EXIF data
        exif_bytes = heif_file.info.get("exif", None)

        if exif_bytes:
            # Parse the EXIF data using piexif
            exif_dict = piexif.load(exif_bytes)

            # Check for the DateTimeOriginal tag (36867 / 0x9003)
            date_str = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
            subsec_str = exif_dict["Exif"].get(piexif.ExifIFD.SubSecTimeOriginal)

            if date_str:
                # Convert bytes to string and format to YYYYMMDDHHMMSS
                date_str = date_str.decode("utf-8")
                datetime_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                
                if subsec_str:
                    # Append hundredths of seconds if available
                    subsec_str = subsec_str.decode("utf-8")
                    formatted_time = datetime_obj.strftime('%Y%m%d%H%M%S') + f"{int(subsec_str):02}"
                else:
                    formatted_time = datetime_obj.strftime('%Y%m%d%H%M%S')
                
                return format_timestamp(formatted_time)
        return None
    except Exception as e:
        print(f"Error getting EXIF data from {heic_path}: {e}")
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

def get_mov_creation_time(mov_path):
    """Extract the creation time from a MOV file using ffmpeg."""
    try:
        # Use ffmpeg to extract metadata
        cmd = ['ffmpeg', '-i', mov_path, '-f', 'ffmetadata', '-']
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        metadata = result.stderr
        
        # Look for the creation_time metadata field
        for line in metadata.splitlines():
            if "creation_time" in line:
                # Extract the timestamp and format it
                date_str = line.split('creation_time   : ')[-1].strip()
                datetime_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                formatted_time = datetime_obj.strftime('%Y%m%d%H%M%S%f')[:-4]  # Hundredths of a second
                return format_timestamp(formatted_time)
        return None
    except Exception as e:
        print(f"Error extracting metadata from {mov_path}: {e}")
        return None

def heic_to_jpg(heic_path, jpg_directory, formatted_time):
    """Convert a single HEIC file to JPG and rename using the date and time."""
    try:
        jpg_path = os.path.join(jpg_directory, f"{formatted_time}.jpg")
        with Image.open(heic_path) as image:
            image.save(jpg_path, "JPEG")
        print(f"Converted {heic_path} to {jpg_path}")
    except Exception as e:
        print(f"Error converting {heic_path} to {jpg_path}: {e}")

def mov_to_mp4(mov_path, jpg_directory, formatted_time):
    """Convert a single MOV file to MP4 and rename using the date and time."""
    try:
        mp4_path = os.path.join(jpg_directory, f"{formatted_time}.mp4")
        with VideoFileClip(mov_path) as video:
            video.write_videofile(mp4_path, codec="libx264", audio_codec="aac")
        print(f"Converted {mov_path} to {mp4_path}")
    except Exception as e:
        print(f"Error converting {mov_path} to {mp4_path}: {e}")

def copy_file(src, jpg_directory, formatted_time):
    """Copy a file from src to jpg_directory and rename it using the date and time."""
    try:
        dst_path = os.path.join(jpg_directory, f"{formatted_time}{os.path.splitext(src)[1]}")
        shutil.copy(src, dst_path)
        print(f"Copied {src} to {dst_path}")
    except Exception as e:
        print(f"Error copying {src} to {dst_path}: {e}")

def bulk_convert(heic_directory, jpg_directory, num_threads=4):
    """Convert and rename all HEIC/MOV files in heic_directory to JPG/MP4 in jpg_directory."""
    os.makedirs(jpg_directory, exist_ok=True)

    tasks = []
    for filename in os.listdir(heic_directory):
        file_path = os.path.join(heic_directory, filename)

        # For HEIC files, try to get the creation time from EXIF data
        if filename.lower().endswith(".heic"):
            formatted_time = get_heic_exif_creation_time(file_path)
            if not formatted_time:  # Fallback to file creation time if EXIF data is missing
                formatted_time = get_file_creation_time(file_path)
        elif filename.lower().endswith(".mov"):
            # Try to get creation time from MOV metadata
            formatted_time = get_mov_creation_time(file_path)
            if not formatted_time:
                formatted_time = get_file_creation_time(file_path)  # Fallback to file mod time
        else:
            # Use file modification time for non-HEIC/MOV files
            formatted_time = get_file_creation_time(file_path)

        if not formatted_time:
            continue  # Skip if unable to retrieve any creation time

        if filename.lower().endswith(".heic"):
            tasks.append((file_path, jpg_directory, formatted_time, heic_to_jpg))
        elif filename.lower().endswith(".mov"):
            tasks.append((file_path, jpg_directory, formatted_time, mov_to_mp4))
        else:
            tasks.append((file_path, jpg_directory, formatted_time, copy_file))

    # Execute tasks in parallel with a specified number of threads
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(task[3], task[0], task[1], task[2]) for task in tasks]
        for future in as_completed(futures):
            pass  # Handle results if needed

# Set the directory containing HEIC files and the output directory for JPG files
heic_directory = '/Volumes/disc0/ItalyPhotos/BrianPhone/photosAll'
jpg_directory  = '/Volumes/disc0/ItalyPhotos/BrianPhone/photosAllJPG'

# Perform the bulk conversion with a specified number of threads
bulk_convert(heic_directory, jpg_directory, num_threads=10)
