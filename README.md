# Payslip Anomaly Detector (MVP)

A local-only tool to detect anomalies in French payslips.

## Features
- **E1**: Missing Critical Fields (Net, Brut, Period, PAS).
- **E2**: Arithmetic Inconsistencies (Brut - Cotis - PAS != Net).
- **E3**: Incoherent values (Negative Net/Brut).
- **Interactive UI**: Visual highlighting of anomalies on the PDF.

## Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- Tesseract OCR (Optional, for scanned PDFs).

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

## Running the Application

### Start Backend
In `backend/` terminal:
```bash
uvicorn app.main:app --reload
```
API will run at `http://localhost:8000`.

### Start Frontend
In `frontend/` terminal:
```bash
npm run dev
```
UI will run at `http://localhost:5173`.

## Testing based on Samples
We have generated sample PDFs in `samples/`:
1. **payslip_ok.pdf**: Should return "Aucune anomalie".
2. **payslip_E1_missing_net.pdf**: Should detect E1 (Missing Net à payer).
3. **payslip_E2_math_error.pdf**: Should detect E2 (Math inconsistency).
4. **payslip_E3_negative.pdf**: Should detect E3 (Negative Net).

## Tech Stack
- **Backend**: FastAPI, pdfplumber, Pydantic.
- **Frontend**: React, Vite, pdfjs-dist.