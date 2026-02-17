from typing import Any, Dict, Optional
from app.core.models import PayslipData

def verifier_coherence_arithmetique(
    salaire_brut: Optional[float],
    net_a_payer: Optional[float],
    total_cotisations: Optional[float] = 0.0,
    prelevement_source: Optional[float] = 0.0,
    tolerance: float = 10.0
) -> Dict[str, Any]:
    """
    Vérifie la cohérence arithmétique globale du bulletin de paie.
    Formule simplifiée : Net à Payer ≈ Brut - Cotisations - PAS

    Args:
        salaire_brut: Montant du salaire brut
        net_a_payer: Montant du net à payer
        total_cotisations: Montant total des cotisations (salariales)
        prelevement_source: Montant du prélèvement à la source
        tolerance: Écart admis pour considérer le calcul comme cohérent

    Returns:
        Dictionnaire contenant les détails du calcul et le statut de l'anomalie.
    """
    
    if salaire_brut is None or net_a_payer is None:
        return {
            "skip": True,
            "reason": "Manque Brut ou Net"
        }

    # Valeurs par défaut si None (pour le calcul)
    brut = salaire_brut
    net = net_a_payer
    cotis = total_cotisations if total_cotisations is not None else 0.0
    pas = prelevement_source if prelevement_source is not None else 0.0

    # Calcul du net théorique
    # Note: Cette formule est une approximation. 
    # Le "Total Cotisations" extrait peut inclure ou non la part patronale selon l'extraction.
    # Ici on suppose que l'on a extrait la part salariale.
    net_calcule = brut - cotis - pas
    
    ecart = abs(net - net_calcule)
    is_anomalie = ecart > tolerance

    return {
        "skip": False,
        "brut": brut,
        "cotisations": cotis,
        "prelevement_source": pas,
        "net_affiche": net,
        "net_calcule": round(net_calcule, 2),
        "ecart": round(ecart, 2),
        "tolerance": tolerance,
        "anomalie": is_anomalie,
        "details": f"Brut ({brut}) - Cotisations ({cotis}) - PAS ({pas}) = {net_calcule:.2f} (Attendu: {net})"
    }
