import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import os
from pathlib import Path
import io
import json

def process_pdf(pdf_path, use_cache=True):
    """Process PDF using Tesseract OCR with caching"""
    try:
        # Setup cache
        cache_dir = Path.home() / '.ocr_cache'
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f"{Path(pdf_path).stem}_ocr.json"
        
        # Check cache
        if use_cache and cache_file.exists():
            print("Using cached result...")
            return json.loads(cache_file.read_text(encoding='utf-8'))

        # Open PDF
        print("Processing PDF...")
        doc = fitz.open(pdf_path)
        text_results = []

        # Process each page
        for page_num in range(len(doc)):
            print(f"Processing page {page_num + 1}/{len(doc)}")
            page = doc.load_page(page_num)
            
            # Try to extract text directly first
            text = page.get_text()
            if text.strip():
                text_results.append(text)
                continue
                
            # If no text found, do OCR
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang='por')
            text_results.append(text)

        # Cache results
        result = "\n".join(text_results)
        if use_cache:
            cache_file.write_text(json.dumps(result), encoding='utf-8')
            
        return result

    except Exception as e:
        print(f"Error processing PDF: {e}")
        return ""

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if __name__ == "__main__":
    pdf_path = "edital_A06_2024.pdf"
    result = process_pdf(pdf_path)
    output_file = "out2.txt"
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(result)
    print(f"Text extracted and saved to {output_file}")

