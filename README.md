
# Photo Processing and Slide Show Creation

## Description
This project provides scripts to automate the processing, renaming, and organizing of images and videos from various sources (e.g., HEIC, MOV, JPG). It also facilitates creating Google Slides presentations using these organized files.

---

## Usage Workflow

### **Step 1: Download Files from iCloud or Other Sources**
Use the iCloud interface (or another source) to download HEIC, MOV, or JPG files to a local directory.

---

### **Step 2: Convert HEIC/MOV Files**
Run the HEIC/MOV conversion script to:
- Convert HEIC files to JPG.
- Convert MOV files to MP4.
- Extract timestamps from EXIF or metadata to rename files in the `YYYYMMDDHHMMSSXX` format.

#### **Command**:
```bash
python heic_mov_conversion.py
```

---

### **Step 3: Rename Standard JPG Files**
If you have JPG files from a standard camera (e.g., SD card), use the renaming script to organize them with the same timestamp format.

#### **Command**:
```bash
python rename_jpg_files.py
```

---

### **Step 4: Upload Files to Google Drive**
Use your preferred method (e.g., drag and drop in the Google Drive web interface or a sync tool) to upload the renamed files to a specific folder structure in Google Drive.

---

### **Step 5: Generate Metadata**
Run the metadata script to:
- Create/append valid and invalid metadata CSVs.
- Parallelize metadata extraction for faster processing.

#### **Command**:
```bash
python metadata_generation.py --config config.yaml
```

#### **Example `config.yaml`**:
```yaml
credentials_path: "path/to/credentials.json"
directories:
  - "google_drive_folder_id_1"
  - "google_drive_folder_id_2"
valid_csv: "valid_images.csv"
invalid_csv: "invalid_images.csv"
```

---

### **Step 6: Create Google Slides Presentation**
Run the slide creation script to generate a presentation using images listed in the `valid_images.csv`.

#### **Command**:
```bash
python create_slideshow.py --config config.yaml
```

#### **Example `config.yaml`**:
```yaml
credentials_path: "path/to/credentials.json"
valid_csv: "valid_images.csv"
```

---

## Future Projects: Integrating Image Size Validation and Reformatting

### **Should we gather image size during the initial HEIC to JPG conversion?**

#### **Advantages**:
- By gathering image sizes upfront, you could immediately identify files exceeding the 10 MB limit, streamlining the later metadata generation process.
- Incorporating image resizing during the HEIC to JPG conversion phase could ensure that files stay within the limit, saving time and storage.

#### **Challenges**:
- Adding resizing during the initial conversion may complicate the script, especially when determining resizing rules (e.g., preserve aspect ratio, reduce quality, etc.).
- You might need to standardize how resizing is handled across different file formats (e.g., HEIC, MOV, JPG).

#### **Recommendation**:
- For future projects, it would be worth considering adding image size validation and optional resizing during the initial conversion. This can be logged in the generated metadata for easy reference. However, it’s important to ensure this step doesn’t degrade the quality of images unnecessarily.

---

## License
[Specify your project's license here.]

---

## Contributing
Contributions are welcome! Please open an issue or submit a pull request with your changes.
