# ===================================================================
# ==       PDF Folder & File Renamer (v6 - Final Syntax Fix)     ==
# ===================================================================
#
# IMPORTANT NOTE FOR LARGE FILES (> 200MB):
# By default, Streamlit limits file uploads to 200MB. To increase this,
# create a folder named `.streamlit` in the same directory as this script.
# Inside that folder, create a file named `config.toml` and add:
#
# [server]
# maxUploadSize = 500  # Sets the limit to 500MB
#
# Then, restart the Streamlit app.
#
# ===================================================================

import streamlit as st
import os
import zipfile
import tempfile
import shutil
import re
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(layout="wide")
st.title('🗂️ PDF Folder & File Renamer')
st.info(
    """
    **Purpose:** This tool automates the renaming of specific folders and PDF files within a zip archive.
    - **Folder Renaming:** Finds folders like `AC001`, `AC002` and renames them to `1`, `2`.
    - **File Renaming (Corrected Logic):** Renames `S03A0010095.pdf` to `S03_1_95.pdf`.
    """
)

# --- UI for File Upload ---
with st.sidebar:
    st.header('1. Upload Your Data')
    st.write("Upload a .zip file containing your 'AC' folders.")
    uploaded_zip = st.file_uploader("Upload Data (.zip)", type="zip")
    st.caption("Note: Large file uploads may take a moment. For files > 200MB, the server configuration must be updated (see script comments for instructions).")

# --- Main Application Area ---
st.header('2. Run the Renaming Process')

if st.button('🚀 Start Renaming', type="primary", disabled=(not uploaded_zip)):
    with tempfile.TemporaryDirectory() as temp_dir:
        
        # --- 1. UNZIP & FIND BASE PATH ---
        with st.spinner('Extracting zip file...'):
            try:
                with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            except Exception as e:
                st.error(f"Error extracting zip file: {e}"); st.stop()

        extracted_contents = os.listdir(temp_dir)
        base_path = temp_dir
        if len(extracted_contents) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_contents[0])):
            base_path = os.path.join(temp_dir, extracted_contents[0])
            st.success(f"Zip extracted. Found single base folder: `{os.path.basename(base_path)}`")
        else:
            st.success("Zip extracted. Found multiple items at the root.")
        
        st.markdown("---")

        # --- INITIAL SCAN REPORT ---
        st.subheader("Initial Scan Results")
        with st.spinner("Scanning extracted contents..."):
            total_dirs, total_files = 0, 0
            for _, dirs, files in os.walk(base_path):
                total_dirs += len(dirs)
                total_files += len(files)
            col1, col2 = st.columns(2)
            col1.metric("Total Folders Found (in all subdirectories)", f"{total_dirs:,}")
            col2.metric("Total Files Found (in all subdirectories)", f"{total_files:,}")
        st.markdown("---")
        
        # --- 2. RENAME FOLDERS ---
        st.subheader("Part 1: Renaming Folders")
        folders_renamed_count = 0
        renamed_folder_map = {} 
        with st.expander("Show Folder Renaming Log", expanded=True):
            for root, dirs, _ in os.walk(base_path):
                for dir_name in list(dirs):
                    if dir_name.upper().startswith('AC'):
                        original_path = os.path.join(root, dir_name)
                        numbers = re.findall(r'\d+', dir_name)
                        if numbers:
                            new_name = str(int(numbers[0]))
                            new_path = os.path.join(root, new_name)
                            if os.path.exists(new_path):
                                st.warning(f"  - ⚠️ Skipped renaming `{dir_name}` because `{new_name}` already exists.")
                                continue
                            try:
                                shutil.move(original_path, new_path)
                                st.write(f"  - ✔️ Renamed Folder: `{dir_name}` → `{new_name}`")
                                folders_renamed_count += 1
                                renamed_folder_map[original_path] = new_path
                                dirs.remove(dir_name) 
                            except Exception as e:
                                st.warning(f"  - ⚠️ Could not rename folder `{dir_name}`: {e}")
        st.success(f"Folder renaming complete. Renamed {folders_renamed_count} folders.")
        st.markdown("---")

        # --- 3. RENAME PDF FILES (WITH CORRECTED LOGIC) ---
        st.subheader("Part 2: Renaming PDF Files")
        files_renamed_count = 0
        final_renamed_paths = list(renamed_folder_map.values())
        with st.expander("Show File Renaming Log", expanded=True):
            if not final_renamed_paths:
                st.info("No 'AC' folders were successfully renamed, so no PDF files to process.")
            
            for folder_path in final_renamed_paths:
                folder_basename = os.path.basename(folder_path)
                st.markdown(f"**Scanning in newly renamed folder: `{folder_basename}`**")
                
                for filename in os.listdir(folder_path):
                    if filename.lower().endswith('.pdf'):
                        match = re.match(r'^(S\d{2})A(\d{3})(\d{4})\.pdf$', filename, re.IGNORECASE)
                        
                        if match:
                            part1 = match.group(1).upper()
                            part2_num = int(match.group(2))
                            part3_num = int(match.group(3))
                            
                            new_filename = f"{part1}_{part2_num}_{part3_num}.pdf"
                            
                            old_file_path = os.path.join(folder_path, filename)
                            new_file_path = os.path.join(folder_path, new_filename)
                            
                            try:
                                os.rename(old_file_path, new_file_path)
                                st.write(f"  - ✔️ Renamed File: `{filename}` → `{new_filename}`")
                                files_renamed_count += 1
                            except Exception as e:
                                st.warning(f"  - ⚠️ Could not rename file `{filename}`: {e}")
                        else:
                            st.write(f"  - Skipping file `{filename}` (pattern not matched).")
        
        st.success(f"File renaming complete. Renamed {files_renamed_count} PDF files.")
        st.markdown("---")

        # --- 4. ZIPPING and DOWNLOAD ---
        st.header("3. Download Your Renamed Data")
        with st.spinner("Zipping results for download..."):
            zip_buffer = BytesIO()
            # ======================= SYNTAX FIX IS HERE =======================
            # Changed the typo "a_file" back to the correct "as zip_file"
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # ==================================================================
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        archive_name = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, archive_name)

        st.download_button(
            label="📥 Download Renamed Data (.zip)",
            data=zip_buffer,
            file_name="renamed_folders_and_files.zip",
            mime="application/zip",
            type="primary"
        )
else:
    st.info("Please upload a zip file to begin the renaming process.")
