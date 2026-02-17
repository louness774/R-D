
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.models import PayslipAnalysis, PayslipData, Anomaly
from app.core.extractor import extract_text_content, group_words_into_lines, extract_payslip_data
from app.core.rules import check_rules
from app.core.rgdu import RGDUParams, load_rgdu_params, save_rgdu_params

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.get("/rgdu-params", response_model=RGDUParams)
def get_rgdu_params():
    return load_rgdu_params()

@app.post("/rgdu-params", response_model=RGDUParams)
def update_rgdu_params(params: RGDUParams):
    save_rgdu_params(params)
    return params

@app.post("/analyze", response_model=PayslipAnalysis)
async def analyze_payslip(file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")
    
    if file.content_type != "application/pdf":
        logger.warning("Invalid file type uploaded.")
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")
    
    try:
        content = await file.read()
        logger.info(f"File size: {len(content)} bytes")
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(status_code=500, detail="Failed to read file")
    
    # 1. Extraction
    try:
        logger.info("Starting extraction...")
        raw_words = extract_text_content(content)
        logger.info(f"Extracted {len(raw_words)} words")
        
        lines = group_words_into_lines(raw_words)
        logger.info(f"Grouped into {len(lines)} lines")
        
        data = extract_payslip_data(lines)
        logger.info("Data extraction complete.")
        # logger.info(f"Extracted data: {data}")
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    # 2. Analysis
    try:
        logger.info("Starting analysis...")
        # Load current parameters for analysis
        rgdu_params = load_rgdu_params()
        anomalies = check_rules(data, rgdu_params)
        logger.info(f"Analysis complete. Found {len(anomalies)} anomalies.")
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    status = "ANOMALIES" if anomalies else "OK"
    
    return PayslipAnalysis(
        status=status,
        anomalies=anomalies,
        extracted_data=data
    )

