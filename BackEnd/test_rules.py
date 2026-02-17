from app.core.models import PayslipData, ExtractedField, TextReference
from app.core.rgdu import RGDUParams
from app.core.rules import check_rules

def test_rules_integration():
    print("Testing Rules Integration...")
    
    # Mock data
    # 1. Valid case (approx)
    params = RGDUParams(smic_mensuel=1823.03)
    
    # Case with Arithmetic Error (E2)
    print("\n--- Testing E2 (Arithmetic) ---")
    data_e2 = PayslipData(
        salaire_brut=ExtractedField(value=3000.0, references=[]),
        net_a_payer=ExtractedField(value=2500.0, references=[]), # Should be less with cotis
        total_cotisations=ExtractedField(value=600.0, references=[]), # 3000 - 600 = 2400. Diff = 100 > 10
        prelevement_source=ExtractedField(value=0.0, references=[])
    )
    anomalies = check_rules(data_e2, params)
    for a in anomalies:
        print(f"[{a.code}] {a.title}: {a.explanation}")
    
    # Case with Negative Value (E3)
    print("\n--- Testing E3 (Consistency) ---")
    data_e3 = PayslipData(
        salaire_brut=ExtractedField(value=-100.0, references=[]),
        net_a_payer=ExtractedField(value=2000.0, references=[])
    )
    anomalies = check_rules(data_e3, params)
    for a in anomalies:
         print(f"[{a.code}] {a.title}: {a.explanation}")

if __name__ == "__main__":
    test_rules_integration()
