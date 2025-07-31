# bot/utils.py

import os
import shutil
import zipfile
import img2pdf
import fitz  # PyMuPDF
from PIL import Image
from natsort import natsorted

# --- Conversion Logic ---

async def convert_cbz_to_pdf(cbz_path: str, output_path: str):
    """Converts a CBZ file to a PDF file."""
    temp_dir = "temp_unzip_cbz"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    try:
        # Unzip the CBZ file
        with zipfile.ZipFile(cbz_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Get all image files and sort them naturally
        image_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif')):
                    image_files.append(os.path.join(root, file))
        
        image_files = natsorted(image_files)

        if not image_files:
            raise ValueError("No images found in the CBZ file.")

        # Convert images to PDF
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_files))
        
        return True
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)

async def convert_pdf_to_cbz(pdf_path: str, output_path: str):
    """Converts a PDF file to a CBZ file."""
    temp_dir = "temp_pdf_extract"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        # Extract images from PDF
        pdf_document = fitz.open(pdf_path)
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap()
            output_image_path = os.path.join(temp_dir, f"page_{page_num+1:04d}.png")
            pix.save(output_image_path)
        pdf_document.close()

        # Create a zip file
        zip_path = output_path.replace('.cbz', '.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)
        
        # Rename zip to cbz
        os.rename(zip_path, output_path)

        return True
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
