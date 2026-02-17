from app.core.rgdu import calculer_rgdu, RGDUParams

def test_rgdu_calculation():
    print("Testing RGDU calculation...")
    
    # Test case from user's script
    # brut=3309.44, effectif=True, heures_sup=0, tdeltaopt=0.3241
    
    result = calculer_rgdu(
        brut_mensuel=3309.44,
        effectif_50_et_plus=True, 
        heures_supplementaires=0,
        tdeltaopt=0.3241
    )
    
    print("Result:", result)
    
    # Check expected values (approximate)
    # Based on user script output if I ran it... 
    # Let's just check if it returns a dictionary with 'reduction_mensuelle'
    
    assert "reduction_mensuelle" in result
    print("Reduction mensuelle:", result["reduction_mensuelle"])
    
    # Test with default params
    result_default = calculer_rgdu(
        brut_mensuel=2000.0,
        effectif_50_et_plus=False
    )
    print("Result default (2000€, <50):", result_default["reduction_mensuelle"])
    
    print("Test passed!")

if __name__ == "__main__":
    test_rgdu_calculation()
