import json
import os
from typing import Any, Dict, Optional
from pydantic import BaseModel

# File path for storing parameters
PARAMS_FILE = "data/rgdu_params.json"

class RGDUParams(BaseModel):
    heures_contractuelles: float = 151.67
    effectif_50_et_plus: bool = True
    smic_mensuel: float = 1823.03
    tdeltaopt: Optional[float] = None

def load_rgdu_params() -> RGDUParams:
    """Loads RGDU parameters from file or returns defaults."""
    if os.path.exists(PARAMS_FILE):
        try:
            with open(PARAMS_FILE, "r") as f:
                data = json.load(f)
            return RGDUParams(**data)
        except Exception as e:
            print(f"Error loading RGDU params: {e}")
            return RGDUParams()
    return RGDUParams()

def save_rgdu_params(params: RGDUParams):
    """Saves RGDU parameters to file."""
    os.makedirs(os.path.dirname(PARAMS_FILE), exist_ok=True)
    with open(PARAMS_FILE, "w") as f:
        json.dump(params.dict(), f, indent=4)

def calculer_rgdu(
    brut_mensuel: float,
    heures_contractuelles: float = 151.67,
    heures_supplementaires: float = 0,
    effectif_50_et_plus: bool = True,
    smic_mensuel: float = 1823.03,
    tdeltaopt: Any = None,
) -> dict:
    """
    Calcule la réduction générale dégressive unique (RGDU) mensuelle.
 
    Args:
        brut_mensuel: Salaire brut total du bulletin (rémunération soumise à cotisations)
        heures_contractuelles: Heures contractuelles mensuelles (défaut 151.67 pour 35h)
        heures_supplementaires: Nombre d'heures supplémentaires du mois
        effectif_50_et_plus: True si entreprise >= 50 salariés, False sinon
        smic_mensuel: SMIC mensuel brut 2026 (défaut 1823.03 €)
        tdeltaopt: Valeur optionnelle pour Tdelta (par défaut None, utilise la valeur standard)
    
    Returns:
        dict avec le détail de chaque étape du calcul
    """
 
    # --- Paramètres selon la taille de l'entreprise ---
    Tmin = 0.0200
    P = 1.75
 
    if effectif_50_et_plus:
        Tdelta = 0.3821  # FNAL à 0.50%
    else:
        Tdelta = 0.3781  # FNAL à 0.10%
    if tdeltaopt is not None:
        Tdelta = tdeltaopt
 
    Tmax = Tmin + Tdelta  # 0.4021 ou 0.3981
 
    # --- Étape 1 : SMIC de référence mensuel (proratisé selon heures contractuelles) ---
    HEURES_TEMPS_PLEIN = 151.67
    
    # Avoid division by zero if HEURES_TEMPS_PLEIN is modified or something weird happens, 
    # though it's hardcoded here.
    smic_reference = round(smic_mensuel * (heures_contractuelles / HEURES_TEMPS_PLEIN), 2)
 
    # --- Étape 2 : Majoration heures supplémentaires ---
    smic_horaire = smic_mensuel / HEURES_TEMPS_PLEIN
    majoration_hs = round(smic_horaire * heures_supplementaires, 2)
 
    # --- Étape 3 : SMIC ajusté (mensuel) ---
    smic_ajuste_mensuel = smic_reference + majoration_hs
 
    # --- Annualisation ---
    smic_annuel = smic_ajuste_mensuel * 12  # 21 876.36 € (≈ 21 876.40 officiel)
    rab = brut_mensuel * 12  # Rémunération annuelle brute
 
    # --- Étape 4 : Vérification éligibilité (brut < 3 × SMIC) ---
    seuil_3_smic = 3 * smic_ajuste_mensuel
    eligible = brut_mensuel < seuil_3_smic
 
    if not eligible:
        return {
            "smic_reference": smic_reference,
            "majoration_hs": round(majoration_hs, 2),
            "smic_ajuste": round(smic_ajuste_mensuel, 2),
            "assiette_brut": brut_mensuel,
            "ratio_smic": round(brut_mensuel / smic_ajuste_mensuel, 3) if smic_ajuste_mensuel else 0,
            "seuil_3_smic": round(seuil_3_smic, 2),
            "eligible": False,
            "coefficient": 0,
            "reduction_mensuelle": 0,
            "parametres": {
                "Tmin": Tmin,
                "Tdelta": Tdelta,
                "Tmax": Tmax,
                "P": P,
                "effectif": "≥ 50" if effectif_50_et_plus else "< 50",
            },
        }
 
    # --- Étape 5 : Ratio salaire / SMIC ---
    ratio_smic = brut_mensuel / smic_ajuste_mensuel if smic_ajuste_mensuel else 0
 
    # --- Étape 6 : Coefficient dégressif ---
    # inner = (1/2) × (3 × SMIC_annuel / RAB - 1)
    if rab <= 0:
        inner = 0 # Avoid division by zero
    else:
        inner = 0.5 * (3 * smic_annuel / rab - 1)
 
    # Si inner <= 0, le salarié est à >= 3 SMIC, pas de réduction au-delà de Tmin
    if inner <= 0:
        coefficient_degressif = 0.0
    else:
        coefficient_degressif = inner ** P
 
    # --- Étape 7 : Taux applicable ---
    # Coefficient = Tmin + (Tdelta × coefficient_dégressif)
    coefficient = Tmin + (Tdelta * coefficient_degressif)
 
    # Plafonnement à Tmax
    coefficient = min(coefficient, Tmax)
 
    # Plancher à Tmin (seuil minimal de 2%) pour rémunération < 3 SMIC
    coefficient = max(coefficient, Tmin)
 
    # Arrondi à 4 décimales (au dix millième le plus proche)
    coefficient = round(coefficient, 4)
 
    # --- Étape 8 : Réduction mensuelle ---
    reduction_mensuelle = round(coefficient * brut_mensuel, 2)
 
    return {
        "smic_reference": smic_reference,
        "majoration_hs": round(majoration_hs, 2),
        "smic_ajuste": round(smic_ajuste_mensuel, 2),
        "smic_annuel": round(smic_annuel, 2),
        "assiette_brut": brut_mensuel,
        "rab": round(rab, 2),
        "ratio_smic": round(ratio_smic, 3),
        "seuil_3_smic": round(seuil_3_smic, 2),
        "eligible": True,
        "inner": round(inner, 6),
        "coefficient_degressif": round(coefficient_degressif, 6),
        "coefficient": coefficient,
        "reduction_mensuelle": reduction_mensuelle,
        "parametres": {
            "Tmin": Tmin,
            "Tdelta": Tdelta,
            "Tmax": Tmax,
            "P": P,
            "effectif": "≥ 50" if effectif_50_et_plus else "< 50",
        },
    }
