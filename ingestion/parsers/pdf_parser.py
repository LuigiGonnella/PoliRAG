"""PDF content parser."""
import fitz #PyMuPDF
from PIL import Image
import pytesseract
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
import os

PAGE_TH = 15

def is_image_based(page, th):
    words = page.get_text("text").strip().split()
    return len(words) < th

def ocr_pdf(page):
    pix = page.get_pixmap(dpi=300)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img)
    return text

def extract_pdf_text(path):
    text = ""
    tables = []
    already_scanned = False
    doc = fitz.open(path)
    filename = os.path.split(path)[-1]
    basename = os.path.splitext(filename)[0]

    for page in doc:
        if is_image_based(page, PAGE_TH):
            page_text = ocr_pdf(page) + "\n"
            text += page_text 

        else:
            present_table = any(item['rects'] or item['lines'] for item in page.get_drawings())


            if present_table and not already_scanned:
                pipeline_options = PdfPipelineOptions(generate_picture_images=True)
                res = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
                    }
                ).convert(path)
                already_scanned = True
                
                page_tables = [table.export_to_markdown() for table in res.document.tables]
                tables += page_tables



            
            page_text = page.get_text("text") + "\n"
            text += page_text

        print(f"DOCUMENT {basename} chunking completed successfully!")

    return text, tables


