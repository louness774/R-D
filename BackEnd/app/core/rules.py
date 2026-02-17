from app.core.models import PayslipData, Anomaly, AnomalyCode, AnomalySeverity, TextReference
from app.core.models import PayslipData, Anomaly, AnomalyCode, AnomalySeverity, TextReference
from app.core.rgdu import RGDUParams, calculer_rgdu
from app.core.arithmetic import verifier_coherence_arithmetique
from app.core.consistency import verifier_valeurs_aberrantes
from typing import List

def check_rules(data: PayslipData, rgdu_params: RGDUParams) -> List[Anomaly]:
    anomalies = []
    
    # --- E1: RGDU / Allegements Consistency ---
    # We use the parameters to calculate the expected RGDU.
    # If the payslip shows an amount for "Allègements" or "Exonérations", we compare.
    # If not, we can only check if it SHOULD have one (eligibility).
    
    if data.salaire_brut and data.salaire_brut.value is not None:
        brut = data.salaire_brut.value
        
        # Calculate theoretical RGDU
        # We assume standard 35h (151.67) and 0 overtime for MVP unless we extract overtime.
        # Ideally we should extract overtime hours too, but for now we use defaults or params.
        calc_result = calculer_rgdu(
            brut_mensuel=brut,
            heures_contractuelles=rgdu_params.heures_contractuelles,
            heures_supplementaires=0, # TODO: Extract from payslip
            effectif_50_et_plus=rgdu_params.effectif_50_et_plus,
            smic_mensuel=rgdu_params.smic_mensuel,
            tdeltaopt=rgdu_params.tdeltaopt
        )
        
        expected_reduction = calc_result.get("reduction_mensuelle", 0.0)
        is_eligible = calc_result.get("eligible", False)
        
        # Check against extracted "allegements"
        if data.allegements and data.allegements.value is not None:
            extracted_reduction = data.allegements.value
            diff = abs(expected_reduction - extracted_reduction)
            
            # Tolerance: 2.00 € (rounding differences)
            if diff > 2.0:
                explanation = (
                    f"Montant détecté : {extracted_reduction} €. "
                    f"Montant calculé (RGDU) : {expected_reduction} €. "
                    f"Paramètres utilisés : SMIC={rgdu_params.smic_mensuel}, "
                    f"Effectif {'≥50' if rgdu_params.effectif_50_et_plus else '<50'}. "
                    f"Écart : {diff:.2f} €."
                )
                anomalies.append(Anomaly(
                    code=AnomalyCode.E1,
                    title="Erreur RGDU (Montant incorrect)",
                    severity=AnomalySeverity.HIGH,
                    explanation=explanation,
                    references=data.allegements.references + data.salaire_brut.references
                ))
        elif is_eligible and expected_reduction > 0:
            # Eligible but no reduction found on payslip?
            # It might be there but not extracted, OR missing.
            # We flag as a potential issue but maybe MEDIUM severity if we are not sure about extraction.
             anomalies.append(Anomaly(
                    code=AnomalyCode.E1,
                    title="Absence de RGDU (Éligibilité détectée)",
                    severity=AnomalySeverity.MEDIUM,
                    explanation=f"Le salarié semble éligible à une RGDU de {expected_reduction:.2f} € (Brut: {brut}), mais aucun montant d'allègement n'a été détecté.",
                    references=data.salaire_brut.references
                ))

    # --- E2: Arithmetic consistency ---
    # Net ≈ Brut - Cotisations - PAS
    # (Simplified check)
    if data.salaire_brut and data.net_a_payer:
        brut = data.salaire_brut.value
        net = data.net_a_payer.value
        cotis = data.total_cotisations.value if data.total_cotisations else 0.0
        pas = data.prelevement_source.value if data.prelevement_source else 0.0

        res_e2 = verifier_coherence_arithmetique(
            salaire_brut=brut,
            net_a_payer=net,
            total_cotisations=cotis,
            prelevement_source=pas,
            tolerance=10.0 # Generous tolerance
        )

        if not res_e2.get("skip") and res_e2.get("anomalie"):
             refs = []
             if data.salaire_brut: refs.extend(data.salaire_brut.references)
             if data.net_a_payer: refs.extend(data.net_a_payer.references)
             if data.total_cotisations: refs.extend(data.total_cotisations.references)
             
             anomalies.append(Anomaly(
                code=AnomalyCode.E2,
                title="Incohérence arithmétique globale",
                severity=AnomalySeverity.MEDIUM,
                explanation=f"Calcul incohérent : {res_e2['details']}",
                references=refs
             ))

    # --- E3: Incoherent values (Negative) ---
    aberrations = verifier_valeurs_aberrantes(data)
    for ab in aberrations:
        anomalies.append(Anomaly(
            code=AnomalyCode.E3,
            title=f"Montant incohérent ({ab['type']})",
            severity=AnomalySeverity.HIGH if ab['field'] == 'salaire_brut' else AnomalySeverity.MEDIUM,
            explanation=ab['message'],
            references=ab['references']
        ))

    return anomalies
