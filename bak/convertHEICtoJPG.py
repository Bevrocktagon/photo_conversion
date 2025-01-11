import os
import shutil
from PIL import Image
from pillow_heif import register_heif_opener
from concurrent.futures import ThreadPoolExecutor, as_completed
from moviepy.editor import VideoFileClip

# Register the HEIC opener for Pillow
register_heif_opener()

def heic_to_jpg(heic_path, jpg_path):
    """Convert a single HEIC file to JPG."""
    try:
        with Image.open(heic_path) as image:
            image.save(jpg_path, "JPEG")
        print(f"Converted {heic_path} to {jpg_path}")
    except Exception as e:
        print(f"Error converting {heic_path} to {jpg_path}: {e}")

def mov_to_mp4(mov_path, mp4_path):
    """Convert a single MOV file to MP4."""
    try:
        with VideoFileClip(mov_path) as video:
            video.write_videofile(mp4_path, codec="libx264", audio_codec="aac")
        print(f"Converted {mov_path} to {mp4_path}")
    except Exception as e:
        print(f"Error converting {mov_path} to {mp4_path}: {e}")

def copy_file(src, dst):
    """Copy a file from src to dst."""
    try:
        shutil.copy(src, dst)
        print(f"Copied {src} to {dst}")
    except Exception as e:
        print(f"Error copying {src} to {dst}: {e}")

def bulk_convert(heic_directory, jpg_directory, num_threads=4):
    """Convert all HEIC files in heic_directory to JPG in jpg_directory using a specified number of threads."""
    os.makedirs(jpg_directory, exist_ok=True)

    tasks = []
    for filename in os.listdir(heic_directory):
        heic_path = os.path.join(heic_directory, filename)
        jpg_path = os.path.join(jpg_directory, os.path.splitext(filename)[0] + ".jpg")
        mov_path = os.path.join(jpg_directory, os.path.splitext(filename)[0] + ".mp4")
        dst_path = os.path.join(jpg_directory, filename)

        if filename.lower().endswith(".heic"):
            tasks.append((heic_path, jpg_path, heic_to_jpg))
        elif filename.lower().endswith(".mov"):
            tasks.append((heic_path, mov_path, mov_to_mp4))
        else:
            tasks.append((heic_path, dst_path, copy_file))

    # Execute tasks in parallel with a custom number of threads
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(task[2], task[0], task[1]) for task in tasks]
        for future in as_completed(futures):
            pass  # Handle results if needed

# Set the directory containing HEIC files and the output directory for JPG files
heic_directory = '/Volumes/disc0/ItalyPhotos/BrianPhone/photosAll'
jpg_directory  = '/Volumes/disc0/ItalyPhotos/BrianPhone/photosAllJPG'

# Perform the bulk conversion with a specified number of threads
bulk_convert(heic_directory, jpg_directory, num_threads=10)
