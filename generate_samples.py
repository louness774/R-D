from fpdf import FPDF
import os

def create_payslip(filename, data, error_mode=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.cell(200, 10, txt="BULLETIN DE PAIE SIMPLIFIE", ln=1, align='C')
    pdf.ln(10)
    
    # Context
    pdf.cell(200, 10, txt=f"Période: {data.get('periode', '01/01/2024 - 31/01/2024')}", ln=1)
    pdf.cell(200, 10, txt="Employé: Jean DUPONT", ln=1)
    pdf.ln(10)
    
    # Body
    # Brut
    brut = data.get('brut', 3000.0)
    pdf.cell(150, 10, txt="Salaire Brut", border=0)
    pdf.cell(40, 10, txt=f"{brut:.2f}".replace('.', ',') + " EUR", ln=1, align='R')
    
    # Cotisations (simplifed)
    cotis = data.get('cotis', 600.0)
    pdf.cell(150, 10, txt="Total Cotisations (Retenues)", border=0)
    pdf.cell(40, 10, txt=f"-{cotis:.2f}".replace('.', ',') + " EUR", ln=1, align='R')
    
    # Net Imposable
    net_imp = data.get('net_imposable', brut - 500) # simplified
    pdf.cell(150, 10, txt="Net Imposable", border=0)
    pdf.cell(40, 10, txt=f"{net_imp:.2f}".replace('.', ',') + " EUR", ln=1, align='R')
    
    # PAS
    pas = data.get('pas', 100.0)
    pdf.cell(150, 10, txt="Prélèvement à la Source (PAS)", border=0)
    pdf.cell(40, 10, txt=f"-{pas:.2f}".replace('.', ',') + " EUR", ln=1, align='R')
    
    pdf.ln(10)
    
    # Net à Payer mechanism
    # Correct math: Net = Brut - Cotis - PAS
    expected_net = brut - cotis - pas
    
    if error_mode == "E2":
        # Introduce Math Error
        displayed_net = expected_net + 50.0 
    elif error_mode == "E1":
        # Missing field (Net)
        displayed_net = None
    elif error_mode == "E3":
        # Negative field
        displayed_net = -100.0
    else:
        displayed_net = expected_net

    if displayed_net is not None:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(150, 10, txt="NET A PAYER", border=0)
        pdf.cell(40, 10, txt=f"{displayed_net:.2f}".replace('.', ',') + " EUR", ln=1, align='R')
    
    pdf.output(filename)
    print(f"Generated {filename}")

if __name__ == "__main__":
    os.makedirs("samples", exist_ok=True)
    
    # 1. Valid Payslip
    create_payslip("samples/payslip_ok.pdf", {"brut": 3000, "cotis": 600, "pas": 100})
    
    # 2. Error E1 (Missing Net)
    create_payslip("samples/payslip_E1_missing_net.pdf", {"brut": 3000}, error_mode="E1")
    
    # 3. Error E2 (Math Error)
    create_payslip("samples/payslip_E2_math_error.pdf", {"brut": 3000, "cotis": 600, "pas": 100}, error_mode="E2")

    # 4. Error E3 (Negative Net)
    create_payslip("samples/payslip_E3_negative.pdf", {"brut": 2000, "cotis": 2500, "pas": 0}, error_mode="E3")
