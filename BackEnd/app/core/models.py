from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class AnomalyCode(str, Enum):
    E1 = "E1"  # Missing critical fields
    E2 = "E2"  # Arithmetic inconsistency
    E3 = "E3"  # Negative or incoherent totals

class AnomalySeverity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class TextReference(BaseModel):
    page: int
    text_snippet: str
    bbox: Optional[List[float]] = None  # [x0, y0, x1, y1]

class Anomaly(BaseModel):
    code: AnomalyCode
    title: str
    severity: AnomalySeverity
    explanation: str
    references: List[TextReference]

class ExtractedField(BaseModel):
    value: Optional[float] = None
    raw_text: Optional[str] = None
    confidence: float = 0.0
    references: List[TextReference] = []

class PayslipData(BaseModel):
    net_a_payer: Optional[ExtractedField] = None
    salaire_brut: Optional[ExtractedField] = None
    total_cotisations: Optional[ExtractedField] = None
    prelevement_source: Optional[ExtractedField] = None
    net_imposable: Optional[ExtractedField] = None
    allegements: Optional[ExtractedField] = None # RGDU / Reductions
    periode: Optional[ExtractedField] = None # Text based

class PayslipAnalysis(BaseModel):
    status: str  # "OK" or "ANOMALIES"
    anomalies: List[Anomaly] = []
    extracted_data: PayslipData
