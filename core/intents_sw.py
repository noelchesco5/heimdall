SYMPTOMS_SW = {
    "homa": ("fever infection", "Moderate"),
    "joto kali": ("fever high temperature", "Moderate"),
    "kikohozi": ("cough respiratory", "Mild"),
    "kukohoa": ("cough respiratory", "Mild"),
    "kichwa kinaniuma": ("headache head pain", "Mild"),
    "maumivu ya kichwa": ("headache head pain", "Mild"),
    "tumbo linaniuma": ("stomach pain abdominal", "Moderate"),
    "maumivu ya tumbo": ("stomach pain abdominal", "Moderate"),
    "kifua kinaniuma": ("chest pain cardiac emergency", "Emergency"),
    "maumivu ya kifua": ("chest pain cardiac emergency", "Emergency"),
    "kupumua kwa shida": ("breathing difficulty respiratory distress", "Emergency"),
    "kupumua vibaya": ("breathing difficulty respiratory distress", "Emergency"),
    "mgongo unaniuma": ("back pain spine", "Mild"),
    "maumivu ya mgongo": ("back pain spine", "Mild"),
    "mguu unaniuma": ("leg pain musculoskeletal", "Mild"),
    "maumivu ya mguu": ("leg pain musculoskeletal", "Mild"),
    "jicho linaniuma": ("eye pain ophthalmology", "Moderate"),
    "sikio linaniuma": ("ear pain otolaryngology", "Moderate"),
    "kuhara": ("diarrhea gastrointestinal", "Moderate"),
    "kutapika": ("vomiting gastrointestinal", "Moderate"),
    "choo kigumu": ("constipation bowel", "Mild"),
    "mfupa umevunjika": ("fracture bone radiograph", "Serious"),
    "gozi nyekundu": ("skin rash dermatology", "Mild"),
    "meno yananiuma": ("toothache dental", "Mild"),
    "koo linaniuma": ("sore throat pharyngitis", "Mild"),
    "pua inaziba": ("nasal congestion sinusitis", "Mild"),
    "uvimbe": ("swelling edema inflammation", "Moderate"),
    "ngozi imeungua": ("bruise contusion skin injury dermatology", "Mild"),
    "ngozi kavu": ("dry skin xerosis dermatology", "Mild"),
    "kavu": ("dry skin xerosis", "Mild"),
    "imeungua": ("bruise contusion skin injury dermatology", "Mild"),
    "jeraha": ("wound ulcer skin lesion", "Moderate"),
    "majipu": ("abscess pus skin infection", "Moderate"),
}

BODY_PARTS = {
    "kichwa": "head",
    "macho": "eyes",
    "masikio": "ears",
    "pua": "nose",
    "mdomo": "mouth",
    "koo": "throat",
    "kifua": "chest",
    "tumbo": "stomach abdomen",
    "mgongo": "back spine",
    "mguu": "leg limb",
    "mkono": "arm limb",
    "jino": "tooth dental",
    "ngozi": "skin dermatology",
    "mfupa": "bone orthopedic",
}

PAIN_VERBS = ["linaniuma", "linauma", "inaniuma", "inauma", "unaniuma", "unauma",
              "naumwa", "imevimba", "limevimba", "umevimba",
              "imeungua", "imejeruhiwa", "limejeruhiwa"]


def detect(text):
    lowered = text.lower()
    found = []
    for phrase, (expansion, severity) in SYMPTOMS_SW.items():
        if phrase in lowered:
            found.append({"intent": phrase, "expansion": expansion, "severity": severity})
    for word, expansion in BODY_PARTS.items():
        if word not in lowered:
            continue
        if any(verb in lowered for verb in PAIN_VERBS):
            found.append({"intent": f"{word} pain", "expansion": expansion, "severity": None})
        else:
            found.append({"intent": word, "expansion": expansion, "severity": None})
    return found
