
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.models import PayslipAnalysis, PayslipData, Anomaly
from app.core.extractor import extract_text_content, group_words_into_lines, extract_payslip_data
from app.core.rules import check_rules

app = FastAPI(title="Payslip Anomaly Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Payslip Anomaly Detector API is running"}

@app.post("/analyze", response_model=PayslipAnalysis)
async def analyze_payslip(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")
    
    content = await file.read()
    
    # 1. Extraction
    try:
        raw_words = extract_text_content(content)
        lines = group_words_into_lines(raw_words)
        data = extract_payslip_data(lines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    # 2. Analysis
    anomalies = check_rules(data)
    
    status = "ANOMALIES" if anomalies else "OK"
    
    return PayslipAnalysis(
        status=status,
        anomalies=anomalies,
        extracted_data=data
    )

