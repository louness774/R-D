from typing import List
from app.core.models import PayslipData, Anomaly, AnomalyCode, AnomalySeverity, TextReference

def check_rules(data: PayslipData) -> List[Anomaly]:
    anomalies = []
    
    # E1: Missing critical fields
    required_fields = {
        "net_a_payer": "Net à payer",
        "salaire_brut": "Salaire brut",
        # "prelevement_source": "Prélèvement à la source", # Not always present if 0
    }
    
    missing = []
    for attr, label in required_fields.items():
        if getattr(data, attr) is None:
            missing.append(label)
            
    if missing:
        anomalies.append(Anomaly(
            code=AnomalyCode.E1,
            title="Champs obligatoires manquants",
            severity=AnomalySeverity.HIGH,
            explanation=f"Les champs suivants n'ont pas été détectés : {', '.join(missing)}.",
            references=[]
        ))

    # E2: Arithmetic consistency
    # Net ≈ Brut - Cotisations - PAS
    if data.salaire_brut and data.net_a_payer:
        brut = data.salaire_brut.value
        net = data.net_a_payer.value
        cotis = data.total_cotisations.value if data.total_cotisations else 0.0
        pas = data.prelevement_source.value if data.prelevement_source else 0.0
        
        # If we have Brut and Net, we expect specific math.
        # But extracted "Total Cotisations" might be ambiguous (Employer vs Employee). 
        # Usually "Net Imposable" ~ Brut - Cotis_Sociales_Deductibles.
        # "Net à Payer" = Net_Imposable - PAS - Non_Deductible_Cotis? No.
        # Simple rule: Net = Brut - Charges_Salariales - PAS (+/- indemnités)
        # MVP: check deviation.
        
        computed_net = brut - cotis - pas
        diff = abs(net - computed_net)
        
        # If difference > 2.0 (tolerance)
        if diff > 5.0: # Generous tolerance for MVP extraction noise
             refs = []
             if data.salaire_brut: refs.extend(data.salaire_brut.references)
             if data.net_a_payer: refs.extend(data.net_a_payer.references)
             if data.total_cotisations: refs.extend(data.total_cotisations.references)
             if data.prelevement_source: refs.extend(data.prelevement_source.references)
             
             anomalies.append(Anomaly(
                code=AnomalyCode.E2,
                title="Incohérence arithmétique",
                severity=AnomalySeverity.MEDIUM,
                explanation=f"Calcul incohérent : Brut ({brut}) - Cotisations ({cotis}) - PAS ({pas}) = {computed_net:.2f}, mais le Net à payer affiché est {net}.",
                references=refs
             ))

    # E3: Incoherent values (Negative)
    # Brut < 0
    if data.salaire_brut and data.salaire_brut.value < 0:
        anomalies.append(Anomaly(
            code=AnomalyCode.E3,
            title="Montant incohérent (Négatif)",
            severity=AnomalySeverity.HIGH,
            explanation=f"Le salaire brut détecté est négatif ({data.salaire_brut.value}).",
            references=data.salaire_brut.references
        ))
        
    # Net < 0
    if data.net_a_payer and data.net_a_payer.value < 0:
        anomalies.append(Anomaly(
            code=AnomalyCode.E3,
            title="Montant incohérent (Négatif)",
            severity=AnomalySeverity.HIGH,
            explanation=f"Le net à payer détecté est négatif ({data.net_a_payer.value}).",
            references=data.net_a_payer.references
        ))
        
    # Brut < Net (rare but possible with refunds, usually anomaly)
    if data.salaire_brut and data.net_a_payer and data.salaire_brut.value < data.net_a_payer.value:
         # simple heuristic check
         pass # disabled for MVP simplicity, focused on negatives

    return anomalies
