import pdfplumber
import tempfile
import os
from typing import List, Dict, Any, Tuple
from app.core.models import TextReference

# Fallback import for OCR (optimization: only import if needed or simple check)
try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

def extract_text_content(file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Extracts text and bounding boxes from a PDF.
    Returns a list of dicts: {'page': int, 'text': str, 'bbox': [x0, y0, x1, y1]}
    """
    extracted_content = []
    
    # Write bytes to a temp file because pdfplumber needs a path or file-like object
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        with pdfplumber.open(tmp_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                words = page.extract_words(x_tolerance=2, y_tolerance=2)
                
                # If very few words, might be scanned -> Try OCR if available
                # Logic: Less than 10 words on a full page usually means image-only
                if len(words) < 10 and pytesseract:
                    # Render page to image
                    # Note: pdfplumber -> to_image() requires ghostscript/imagemagick usually, 
                    # but we can try simple extraction or just skip if complex dependencies are missing.
                    # For MVP, if pdfplumber fails to get words, we mark as needy of OCR.
                    # Implementing robust OCR requires poppler installed. 
                    # We will assume text-based PDF for MVP primarily, but add a stub for OCR.
                    pass 

                for w in words:
                    # pdfplumber bbox: (x0, top, x1, bottom)
                    # We standardise to [x0, y0, x1, y1] where y0 is top
                    bbox = [float(w['x0']), float(w['top']), float(w['x1']), float(w['bottom'])]
                    extracted_content.append({
                        "page": page_num,
                        "text": w['text'],
                        "bbox": bbox
                    })
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return extracted_content

def group_words_into_lines(extracted_words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Simple heuristic to re-group words into lines based on vertical position.
    """
    # Sort by page, then by y0 (top)
    extracted_words.sort(key=lambda x: (x['page'], x['bbox'][1], x['bbox'][0]))
    
    lines = []
    current_line = []
    current_y = -1
    current_page = -1
    TOLERANCE = 3 # pixels

    for word in extracted_words:
        if word['page'] != current_page:
            if current_line:
                lines.append(_merge_line(current_line))
            current_line = [word]
            current_page = word['page']
            current_y = word['bbox'][1]
        elif abs(word['bbox'][1] - current_y) <= TOLERANCE:
            current_line.append(word)
        else:
            if current_line:
                lines.append(_merge_line(current_line))
            current_line = [word]
            current_y = word['bbox'][1]
            
    if current_line:
        lines.append(_merge_line(current_line))
        
    return lines

def _merge_line(words: List[Dict[str, Any]]) -> Dict[str, Any]:
    text = " ".join([w['text'] for w in words])
    page = words[0]['page']
    # Union bbox
    x0 = min(w['bbox'][0] for w in words)
    y0 = min(w['bbox'][1] for w in words)
    x1 = max(w['bbox'][2] for w in words)
    y1 = max(w['bbox'][3] for w in words)
    
    return {
        "page": page,
        "text": text,
        "bbox": [x0, y0, x1, y1]
    }
    

from app.core.models import PayslipData, ExtractedField, TextReference
from app.core.normalizer import parse_french_amount, normalize_key
import re

def extract_payslip_data(lines: List[Dict[str, Any]]) -> PayslipData:
    data = PayslipData()
    
    # regex patterns for keys
    patterns = {
        "net_a_payer": [r"netapayer", r"netpaye", r"resteapayer"],
        "salaire_brut": [r"salairebrut", r"bruttotal", r"totalbrut", r"brutimposable"], # brut imposable is different but often proxies brut
        "net_imposable": [r"netimposable", r"netfiscal", r"netapdeclarer"],
        "prelevement_source": [r"impotsurserevenu", r"prelevementalasource", r"pas"],
        "total_cotisations": [r"totalcotisations", r"totalretenues", r"totalcharges"],
        "allegements": [r"allegements", r"exonerations", r"reductiongenerale", r"rgdu", r"allgt"],
        "periode": [r"periode"]
    }

    # Best effort matching: look for line containing key, then find number in that line
    # Iterate through all lines
    for line in lines:
        text_norm = normalize_key(line['text'])
        original_text = line['text']
        
        for field, regexes in patterns.items():
            # If field already found with high confidence, skip (simple logic: first match wins or bottom-up?)
            # Usually Net to Pay is at the bottom, so bottom-up might be better?
            # For now, top-down.
            
            # Check if any regex matches
            if any(re.search(p, text_norm) for p in regexes):
                # Try to find a number in this line
                # We split by space and try to parse the last plausible number
                # "Net à payer       1 234,56 €"
                
                # Heuristic: look for the last number in the line
                # Split by spaces?
                # Use regex to find potential amount patterns in the original text
                amount_candidates = re.findall(r'[\d\s\.,]+', original_text)
                # Filter candidates that look like amounts (have digit, maybe comma/dot)
                valid_candidates = []
                for cand in amount_candidates:
                    val = parse_french_amount(cand)
                    if val is not None:
                        valid_candidates.append(val)
                
                if valid_candidates:
                    # Assume the last number is the value (common in payslips: label ...... value)
                    value = valid_candidates[-1]
                    
                    # Create field
                    field_obj = ExtractedField(
                        value=value,
                        raw_text=original_text,
                        confidence=0.8,
                        references=[TextReference(
                            page=line['page'],
                            text_snippet=original_text,
                            bbox=line['bbox']
                        )]
                    )
                    
                    # specific assignment
                    current_val = getattr(data, field)
                    # If we haven't found it yet, or this one looks "better" (e.g. "Total Brut" vs "Brut")
                    # For MVP, first match? Or last match? 
                    # "Net à payer" is usually at the bottom.
                    # "Salaire Brut" usually at top.
                    if current_val is None:
                        setattr(data, field, field_obj)
                    elif field == "net_a_payer":
                         # Overwrite if we find another "net à payer" lower down?
                         setattr(data, field, field_obj)
                         
    return data