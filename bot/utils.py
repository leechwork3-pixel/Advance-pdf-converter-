# bot/utils.py

import os
import shutil
import zipfile
import asyncio
import subprocess
from natsort import natsorted
import fitz  # PyMuPDF

# --- E-book Conversion Logic ---

async def convert_with_calibre(input_path: str, output_path: str):
    """
    Uses Calibre's `ebook-convert` command-line tool to convert e-books.
    This runs in a separate thread to avoid blocking the bot.
    """
    command = ['ebook-convert', input_path, output_path]
    
    def run_conversion():
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if process.returncode != 0:
            raise Exception(f"Calibre conversion failed: {process.stderr}")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_conversion)
    return True

async def convert_pdf_to_cbz(pdf_path: str, output_path: str):
    """Converts a PDF file to a CBZ file."""
    temp_dir = f"temp_extract_{os.path.basename(pdf_path)}"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        pdf_doc = fitz.open(pdf_path)
        for page_num in range(len(pdf_doc)):
            page = pdf_doc.load_page(page_num)
            pix = page.get_pixmap()
            pix.save(os.path.join(temp_dir, f"page_{page_num+1:04d}.png"))
        pdf_doc.close()

        zip_path = output_path.replace('.cbz', '.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in natsorted(os.listdir(temp_dir)):
                zipf.write(os.path.join(temp_dir, file), arcname=file)
        
        os.rename(zip_path, output_path)
        return True
    finally:
        shutil.rmtree(temp_dir)
        
