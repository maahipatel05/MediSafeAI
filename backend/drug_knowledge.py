"""
Drug Knowledge Base - Medication Classes and Synonyms
Critical for improving retrieval from 60% to 90%+
"""

# Medication Class Mappings
DRUG_CLASSES = {
    # Anticoagulants
    'anticoagulant': ['warfarin', 'heparin', 'apixaban', 'rivaroxaban', 'dabigatran', 'enoxaparin'],
    'blood thinner': ['warfarin', 'heparin', 'aspirin', 'clopidogrel', 'apixaban', 'rivaroxaban'],
    
    # NSAIDs
    'nsaid': ['ibuprofen', 'naproxen', 'diclofenac', 'celecoxib', 'indomethacin', 'ketorolac', 'meloxicam'],
    'anti-inflammatory': ['ibuprofen', 'naproxen', 'aspirin', 'diclofenac', 'celecoxib'],
    
    # SSRIs
    'ssri': ['fluoxetine', 'sertraline', 'paroxetine', 'citalopram', 'escitalopram', 'fluvoxamine'],
    'antidepressant': ['fluoxetine', 'sertraline', 'paroxetine', 'citalopram', 'escitalopram', 'amitriptyline', 'venlafaxine'],
    
    # Antihypertensives
    'antihypertensive': ['lisinopril', 'amlodipine', 'metoprolol', 'losartan', 'hydrochlorothiazide', 'atenolol'],
    'blood pressure medication': ['lisinopril', 'amlodipine', 'metoprolol', 'losartan', 'hydrochlorothiazide'],
    'ace inhibitor': ['lisinopril', 'enalapril', 'ramipril', 'captopril', 'benazepril'],
    'beta blocker': ['metoprolol', 'atenolol', 'propranolol', 'carvedilol', 'bisoprolol'],
    'calcium channel blocker': ['amlodipine', 'diltiazem', 'nifedipine', 'verapamil'],
    
    # Diabetes medications
    'antidiabetic': ['metformin', 'insulin', 'glipizide', 'glyburide', 'pioglitazone', 'sitagliptin'],
    'diabetes medication': ['metformin', 'insulin', 'glipizide', 'glyburide'],
    
    # Antibiotics
    'antibiotic': ['amoxicillin', 'azithromycin', 'ciprofloxacin', 'doxycycline', 'penicillin', 'cephalexin'],
    
    # Statins
    'statin': ['atorvastatin', 'simvastatin', 'rosuvastatin', 'pravastatin', 'lovastatin', 'fluvastatin'],
    'cholesterol medication': ['atorvastatin', 'simvastatin', 'rosuvastatin', 'pravastatin'],
}

# Drug Name Synonyms
DRUG_SYNONYMS = {
    # Common medications
    'acetaminophen': ['paracetamol', 'tylenol', 'panadol'],
    'paracetamol': ['acetaminophen', 'tylenol', 'panadol'],
    'aspirin': ['acetylsalicylic acid', 'asa', 'bayer'],
    'ibuprofen': ['advil', 'motrin', 'nurofen'],
    'warfarin': ['coumadin', 'jantoven'],
    'metformin': ['glucophage', 'fortamet'],
    'atorvastatin': ['lipitor'],
    'simvastatin': ['zocor'],
    'lisinopril': ['prinivil', 'zestril'],
    'amlodipine': ['norvasc'],
    'metoprolol': ['lopressor', 'toprol'],
    'omeprazole': ['prilosec'],
    'fluoxetine': ['prozac'],
    'sertraline': ['zoloft'],
    'alprazolam': ['xanax'],
    'lorazepam': ['ativan'],
    'zolpidem': ['ambien'],
    
    # Generic to brand
    'insulin': ['humalog', 'novolog', 'lantus', 'levemir'],
}

def expand_drug_query(query_text):
    """
    Expand query with drug classes and synonyms
    This is the KEY to improving from 60% to 90%+
    """
    query_lower = query_text.lower()
    expansions = []
    
    # Check for drug classes
    for drug_class, members in DRUG_CLASSES.items():
        if drug_class in query_lower:
            expansions.extend(members[:3])  # Add top 3 drugs from class
    
    # Check for synonyms
    for drug, synonyms in DRUG_SYNONYMS.items():
        if drug in query_lower:
            expansions.extend(synonyms[:2])  # Add synonyms
    
    # Create expanded query
    if expansions:
        expanded = f"{query_text} {' '.join(expansions)}"
        return expanded
    
    return query_text


def get_drug_class_info(drug_name):
    """Get information about which class a drug belongs to"""
    drug_lower = drug_name.lower()
    
    for class_name, members in DRUG_CLASSES.items():
        if drug_lower in members:
            return class_name
    
    return None
