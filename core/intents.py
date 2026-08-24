from . import config
from . import intents_sw

SYMPTOMS = {
    "fever": ("infection fever", "Moderate"),
    "cough": ("respiratory cough", "Mild"),
    "headache": ("head pain neurology", "Mild"),
    "stomach pain": ("abdominal gastrointestinal", "Moderate"),
    "chest pain": ("cardiac chest", "Emergency"),
    "breathing difficulty": ("pulmonary respiratory distress", "Emergency"),
    "shortness of breath": ("pulmonary respiratory distress", "Emergency"),
    "back pain": ("spine musculoskeletal", "Mild"),
    "leg pain": ("lower limb musculoskeletal", "Mild"),
    "eye pain": ("ophthalmology eye", "Moderate"),
    "ear pain": ("otolaryngology ear", "Moderate"),
    "diarrhea": ("gastrointestinal", "Moderate"),
    "vomiting": ("gastrointestinal nausea", "Moderate"),
    "constipation": ("gastrointestinal bowel", "Mild"),
    "broken bone": ("fracture radiograph orthopedic", "Serious"),
    "fracture": ("fracture radiograph orthopedic", "Serious"),
    "rash": ("dermatology skin eruption rash", "Mild"),
    "sore": ("skin ulcer wound lesion", "Mild"),
    "blister": ("blister vesicular skin lesion dermatology", "Mild"),
    "burn": ("thermal burn wound skin injury", "Serious"),
    "scald": ("scald hot liquid burn skin injury", "Serious"),
    "bruise": ("bruise contusion hematoma skin", "Mild"),
    "toothache": ("dental oral", "Mild"),
    "sore throat": ("pharyngitis throat", "Mild"),
    "sinus infection": ("sinusitis nasal", "Mild"),
    "insomnia": ("sleep disorder", "Mild"),
    "swelling": ("edema inflammation", "Moderate"),
}

MODALITIES = {
    "xray": ("radiograph x-ray", None),
    "x-ray": ("radiograph x-ray", None),
    "ct scan": ("computed tomography ct", None),
    "mri": ("magnetic resonance imaging mri", None),
    "ultrasound": ("ultrasonography sonography", None),
    "scan": ("medical imaging scan", None),
    "biopsy": ("histopathology biopsy microscopy", None),
    "blood test": ("hematology laboratory", None),
    "endoscopy": ("endoscopy colonoscopy", None),
}

EMERGENCY_TERMS = {"chest pain", "breathing difficulty", "shortness of breath"}


def detect(text: str):
    lowered = text.lower()
    found = []
    seen = set()
    for phrase, (expansion, severity) in SYMPTOMS.items():
        if phrase in lowered:
            found.append({"intent": phrase, "expansion": expansion, "severity": severity})
            seen.add(expansion)
    for term, (expansion, _) in MODALITIES.items():
        if term in lowered:
            found.append({"intent": term, "expansion": expansion, "severity": None})
            seen.add(expansion)
    for extra in intents_sw.detect(text):
        if extra["expansion"] not in seen:
            found.append(extra)
            seen.add(extra["expansion"])
    return found


def is_emergency(intents):
    return any(i["intent"] in EMERGENCY_TERMS or i["severity"] == "Emergency" for i in intents)


def retrieval_terms(intents):
    return " ".join(i["expansion"] for i in intents)


def guidance(intents):
    if not intents:
        return ""
    lines = []
    for i in intents:
        sev = i["severity"]
        if sev == "Emergency":
            lines.append(f"Possible {i['intent']}: seek emergency care immediately.")
        elif sev == "Serious":
            lines.append(f"Possible {i['intent']}: hospital evaluation recommended.")
        elif sev == "Moderate":
            lines.append(f"Possible {i['intent']}: see a doctor soon.")
        elif sev == "Mild":
            lines.append(f"Possible {i['intent']}: self-care, see a doctor if it persists.")
    return "\n".join(lines)
