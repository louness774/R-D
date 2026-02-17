from typing import Any, Dict, List, Optional
from app.core.models import PayslipData

def verifier_valeurs_aberrantes(data: PayslipData) -> List[Dict[str, Any]]:
    """
    Vérifie la présence de valeurs aberrantes (négatives ou incohérentes).
    
    Args:
        data: Les données extraites du bulletin de paie.

    Returns:
        Liste d'anomalies détectées (chaque anomalie est un dict).
    """
    anomalies_found = []

    # Vérification Salaire Brut Négatif
    if data.salaire_brut and data.salaire_brut.value is not None:
        if data.salaire_brut.value < 0:
            anomalies_found.append({
                "type": "NEGATIF",
                "field": "salaire_brut",
                "value": data.salaire_brut.value,
                "message": f"Le salaire brut détecté est négatif ({data.salaire_brut.value}).",
                "references": data.salaire_brut.references
            })

    # Vérification Net à Payer Négatif
    if data.net_a_payer and data.net_a_payer.value is not None:
        if data.net_a_payer.value < 0:
            anomalies_found.append({
                "type": "NEGATIF",
                "field": "net_a_payer",
                "value": data.net_a_payer.value,
                "message": f"Le net à payer détecté est négatif ({data.net_a_payer.value}).",
                "references": data.net_a_payer.references
            })

    return anomalies_found
