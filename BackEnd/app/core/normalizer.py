import re
from typing import Optional

def parse_french_amount(text: str) -> Optional[float]:
    """
    Parses a monetary string like '1 234,56 €' or '1.200,50' into float.
    Handles space/dot as thousands separator and comma as decimal separator.
    """
    if not text:
        return None
    
    # Remove currency symbol and whitespace
    clean = text.replace('€', '').replace('EUR', '').strip()
    
    # Remove ALL spaces
    clean = re.sub(r'\s+', '', clean)
    
    # Case: "1.234,56" -> remove dot, replace comma
    if '.' in clean and ',' in clean:
        clean = clean.replace('.', '').replace(',', '.')
    # Case: "1234,56" -> replace comma
    elif ',' in clean:
        clean = clean.replace(',', '.')
    # Case: "1 234.56" (unlikely in FR but possible in some software) -> keep dot
    
    try:
        return float(clean)
    except ValueError:
        return None

def normalize_key(text: str) -> str:
    """Normalize text for key matching (lowercase, no accents, no special chars)"""
    import unicodedata
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^a-z0-9]', '', text)
    
