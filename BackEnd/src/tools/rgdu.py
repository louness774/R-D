from typing import Any
"""
Calcul de la Réduction Générale Dégressive Unique (RGDU) 2026
Selon le décret n°2025-887 du 4 septembre 2025
"""


def calculer_rgdu(
    brut_mensuel: float,
    heures_contractuelles: float = 151.67,
    heures_supplementaires: float = 0,
    effectif_50_et_plus: bool = True,
    smic_mensuel: float = 1823.03,
    tdeltaopt:Any = None,
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
            "ratio_smic": round(brut_mensuel / smic_ajuste_mensuel, 3),
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
    ratio_smic = brut_mensuel / smic_ajuste_mensuel

    # --- Étape 6 : Coefficient dégressif ---
    # inner = (1/2) × (3 × SMIC_annuel / RAB - 1)
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


def afficher_resultat(result: dict) -> None:
    """Affiche le détail du calcul RGDU étape par étape."""
    p = result["parametres"]
    print("=" * 60)
    print(f"CALCUL RGDU 2026 — Entreprise {p['effectif']} salariés")
    print(f"Tmin={p['Tmin']}  Tdelta={p['Tdelta']}  Tmax={p['Tmax']}  P={p['P']}")
    print("=" * 60)

    print(f"\n1. SMIC de référence          : {result['smic_reference']:>10.2f} €")
    print(f"2. Majoration heures sup       : {result['majoration_hs']:>10.2f} €")
    print(f"3. SMIC ajusté                 : {result['smic_ajuste']:>10.2f} €")
    print(f"4. Assiette (brut)             : {result['assiette_brut']:>10.2f} €")
    print(f"5. Ratio salaire / SMIC        : {result['ratio_smic']:>10.3f} × SMIC")
    print(f"   Seuil 3 SMIC                : {result['seuil_3_smic']:>10.2f} €")
    print(f"   Éligible                    : {'Oui' if result['eligible'] else 'Non'}")

    if result["eligible"] and result["coefficient"] > 0:
        print(f"6. Coefficient dégressif       : {result['coefficient_degressif']:>10.6f}")
        print(f"   (inner = {result['inner']:.6f}, inner^{p['P']} = {result['coefficient_degressif']:.6f})")
        print(f"7. Taux applicable (arrondi 4d): {result['coefficient']:>10.4f}")
        print(f"8. Réduction du mois           : {result['reduction_mensuelle']:>10.2f} €")
    else:
        print(f"\n   Pas de réduction applicable.")

    print()


# ===== TESTS =====
if __name__ == "__main__":

    print("TEST 1")
    r1 = calculer_rgdu(brut_mensuel=3309.44, effectif_50_et_plus=True, heures_supplementaires=0,tdeltaopt=0.3241)
    afficher_resultat(r1)

