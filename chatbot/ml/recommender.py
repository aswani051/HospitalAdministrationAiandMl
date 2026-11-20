"""
Aswani Hospital - AI Department Recommender Engine
Loads the trained Scikit-learn TF-IDF model and maps predictions to SQLite database departments.
Includes emergency symptom detection, confidence estimation, and safety disclaimers.
"""

import os
import re
import string
import logging
import joblib
import numpy as np

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(
    BASE_DIR, "chatbot", "ml", "saved_models", "department_recommender.joblib"
)

# Cached model instance
_MODEL_ARTIFACT = None


# Emergency red-flag patterns requiring immediate medical care
EMERGENCY_KEYWORDS = [
    r"\b(crushing chest pain|chest agony|heart attack)\b",
    r"\b(unable to breathe|can't breathe|cannot breathe|severe suffocation|gasping for air)\b",
    r"\b(coughing up blood|vomiting blood|massive bleeding|profuse bleeding)\b",
    r"\b(stroke|face droop|sudden paralysis|slurred speech sudden|hemiplegia)\b",
    r"\b(unconscious|loss of consciousness|passed out completely|unresponsive)\b",
    r"\b(swallowed poison|poisoning|chemical ingestion|snake bite)\b",
    r"\b(severe head trauma|skull fracture|severe concussion bleeding from ear)\b",
]

# Mapping between canonical ML department classes and SQLite database department search terms
DB_DEPARTMENT_MAPPINGS = {
    "General Medicine": ["General", "General Medicine"],
    "Orthopaedics": ["Orthopedic Surgeon", "Orthopaedics", "Orthopedics"],
    "Cardiology": ["Cardiology", "Cardiologist"],
    "Dermatology": ["Dermatology", "Dermatologist"],
    "Neurology": ["Neurologist", "Neurology"],
    "ENT": ["ENT", "Ear Nose Throat", "Otolaryngology"],
    "Paediatrics": ["Paediatrics", "Pediatrics", "Pediatrician"],
    "Gynaecology": ["Gynaecology", "Gynecology", "Obstetrics & Gynaecology"],
}

# Educational department descriptions & common care scopes
DEPARTMENT_GUIDES = {
    "General Medicine": {
        "title": "General Medicine",
        "description": "Specializes in comprehensive diagnosis and treatment of acute and chronic adult illnesses, fevers, infections, metabolic disorders, and routine health evaluations.",
        "common_reasons": ["Fever & chills", "Fatigue & weakness", "Viral & bacterial infections", "General physical health checkup"],
        "icon": "fa-stethoscope"
    },
    "Orthopaedics": {
        "title": "Orthopaedics & Joint Care",
        "description": "Specializes in conditions affecting bones, joints, ligaments, tendons, spine, and musculoskeletal trauma or sports injuries.",
        "common_reasons": ["Knee, back & hip joint pain", "Bone fractures & sprains", "Ligament tears & sports injuries", "Arthritis & mobility issues"],
        "icon": "fa-bone"
    },
    "Cardiology": {
        "title": "Cardiology & Heart Health",
        "description": "Specializes in heart disorders, cardiovascular conditions, chest symptoms, hypertension, arrhythmias, and cardiac wellness.",
        "common_reasons": ["Chest pain & pressure", "Heart palpitations & fluttering", "Shortness of breath on exertion", "Hypertension & cardiovascular evaluation"],
        "icon": "fa-heart-pulse"
    },
    "Dermatology": {
        "title": "Dermatology & Skin Health",
        "description": "Specializes in diseases and conditions of the skin, hair, nails, allergic skin reactions, acne, and cutaneous health.",
        "common_reasons": ["Skin rashes & itching", "Eczema & psoriasis", "Acne & hair loss", "Suspicious moles & skin lesions"],
        "icon": "fa-hand-dots"
    },
    "Neurology": {
        "title": "Neurology & Brain Care",
        "description": "Specializes in disorders of the central and peripheral nervous system, brain, spinal cord, nerves, migraines, and movement disorders.",
        "common_reasons": ["Severe headaches & migraines", "Numbness & tingling sensation", "Dizziness, vertigo & balance issues", "Tremors & seizures"],
        "icon": "fa-brain"
    },
    "ENT": {
        "title": "ENT (Ear, Nose & Throat)",
        "description": "Specializes in conditions affecting the ear, hearing, nasal passages, sinuses, pharynx, larynx, and throat disorders.",
        "common_reasons": ["Ear pain & hearing reduction", "Severe sore throat & difficulty swallowing", "Sinus pressure & nasal blockage", "Tinnitus & voice hoarseness"],
        "icon": "fa-head-side-cough"
    },
    "Paediatrics": {
        "title": "Paediatrics & Child Health",
        "description": "Specializes in medical care for infants, children, and adolescents, including childhood illnesses, growth monitoring, and vaccinations.",
        "common_reasons": ["Child & infant fever", "Persistent vomiting or diarrhea in kids", "Childhood rashes & infections", "Routine immunization & growth evaluation"],
        "icon": "fa-baby"
    },
    "Gynaecology": {
        "title": "Gynaecology & Women's Health",
        "description": "Specializes in female reproductive health, pregnancy care, menstrual irregularities, pelvic health, and menopause management.",
        "common_reasons": ["Irregular or painful periods", "Pelvic pain & cramps", "Pregnancy & prenatal consultations", "PCOS & hormonal concerns"],
        "icon": "fa-person-pregnant"
    },
}

SAFETY_DISCLAIMER = (
    "Medical Disclaimer: This recommendation is generated by an automated AI model for informational "
    "and hospital navigation purposes only. It is NOT a clinical diagnosis, medical prescription, or "
    "treatment plan. If you are experiencing severe pain, difficulty breathing, or sudden emergency symptoms, "
    "please visit our Emergency Department immediately or call our 24/7 emergency hotline at +91 98765 43210."
)


def get_model():
    """
    Load and cache the trained Scikit-learn model artifact in memory.
    Ensures subsequent predictions take less than 2 milliseconds.
    """
    global _MODEL_ARTIFACT
    if _MODEL_ARTIFACT is None:
        if not os.path.exists(MODEL_PATH):
            logger.error("Model file not found at %s. Please run train_model.py first.", MODEL_PATH)
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Train the model first.")
        logger.info("Loading Scikit-learn department recommender model from %s...", MODEL_PATH)
        _MODEL_ARTIFACT = joblib.load(MODEL_PATH)
    return _MODEL_ARTIFACT


def clean_text(text: str) -> str:
    """
    Preprocess user input: lowercase, strip punctuation, remove extra whitespace.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def check_emergency(text: str) -> bool:
    """
    Rule-based safety filter to detect acute red-flag emergency symptoms.
    """
    text_lower = text.lower()
    for pattern in EMERGENCY_KEYWORDS:
        if re.search(pattern, text_lower):
            return True
    return False


def resolve_database_department(canonical_name: str):
    """
    Match the predicted canonical department name against the Django Department table in SQLite.
    Returns: (Department model instance or None, formatted booking url, list of doctors)
    """
    try:
        from home.models import Department, Doctor
        search_terms = DB_DEPARTMENT_MAPPINGS.get(canonical_name, [canonical_name])

        dept = None
        for term in search_terms:
            dept = Department.objects.filter(name__iexact=term).first()
            if dept:
                break

        # If not found yet, create or fallback to exact canonical name
        if not dept:
            dept = Department.objects.filter(name__icontains=canonical_name).first()

        if dept:
            doctors = list(Doctor.objects.filter(dep_name=dept).values('id', 'doc_name', 'doc_spec'))
            booking_url = f"/booking/?department_id={dept.id}&dept={dept.name}"
            return {
                "id": dept.id,
                "name": dept.name,
                "description": dept.description,
                "doctors": doctors,
                "booking_url": booking_url
            }
    except Exception as e:
        logger.exception("Error querying SQLite Department model: %s", e)

    # Fallback default booking url if DB query encounters issues
    return {
        "id": None,
        "name": canonical_name,
        "description": DEPARTMENT_GUIDES.get(canonical_name, {}).get("description", ""),
        "doctors": [],
        "booking_url": f"/booking/?dept={canonical_name}"
    }


def recommend_department(symptoms_text: str) -> dict:
    """
    Core Recommendation Function.
    Accepts:
        symptoms_text (str): Patient-described symptoms or health complaints.
    Returns:
        dict: Recommendation result with department name, confidence, db mapping,
              booking url, emergency flags, and medical disclaimer.
    """
    raw_input = (symptoms_text or "").strip()

    if not raw_input:
        return {
            "success": False,
            "error": "Please describe your symptoms so we can recommend the appropriate department.",
            "code": "EMPTY_INPUT"
        }

    if len(raw_input) < 3:
        return {
            "success": False,
            "error": "The symptom description is too brief. Please provide a little more detail about how you feel.",
            "code": "INPUT_TOO_SHORT"
        }

    # Emergency symptoms check
    is_emergency = check_emergency(raw_input)

    # Clean text for vectorization
    cleaned = clean_text(raw_input)
    if not cleaned:
        cleaned = raw_input.lower()

    # Load ML pipeline
    try:
        artifact = get_model()
        pipeline = artifact['pipeline']
        classes = artifact['classes']

        # Inference
        pred_label = pipeline.predict([cleaned])[0]
        probabilities = pipeline.predict_proba([cleaned])[0]

        # Top prediction confidence
        top_idx = list(classes).index(pred_label)
        confidence = float(probabilities[top_idx])

        # Secondary recommendation
        sorted_indices = np.argsort(probabilities)[::-1]
        secondary = []
        for idx in sorted_indices[1:3]:
            sec_prob = float(probabilities[idx])
            if sec_prob >= 0.15:  # meaningful threshold
                sec_dept = classes[idx]
                secondary.append({
                    "department": sec_dept,
                    "confidence": round(sec_prob * 100, 1),
                    "info": DEPARTMENT_GUIDES.get(sec_dept, {})
                })

    except Exception as e:
        logger.exception("ML prediction error: %s", e)
        # Fallback to General Medicine on model error
        pred_label = "General Medicine"
        confidence = 0.50
        secondary = []

    # Resolve database department record
    db_dept = resolve_database_department(pred_label)
    dept_guide = DEPARTMENT_GUIDES.get(pred_label, {})

    # Build response payload
    return {
        "success": True,
        "department": pred_label,
        "confidence_percentage": round(confidence * 100, 1),
        "is_emergency": is_emergency,
        "emergency_message": (
            "⚠️ URGENT MEDICAL ATTENTION ADVISED: Your symptoms may indicate an acute or critical condition. "
            "Please seek immediate medical care at our 24/7 Emergency Department or call +91 98765 43210 immediately."
            if is_emergency else None
        ),
        "department_details": {
            "title": dept_guide.get("title", pred_label),
            "description": dept_guide.get("description", db_dept.get("description", "")),
            "common_reasons": dept_guide.get("common_reasons", []),
            "icon": dept_guide.get("icon", "fa-hospital")
        },
        "database": {
            "department_id": db_dept.get("id"),
            "department_name": db_dept.get("name"),
            "doctors": db_dept.get("doctors", []),
            "booking_url": db_dept.get("booking_url")
        },
        "secondary_recommendations": secondary,
        "safety_disclaimer": SAFETY_DISCLAIMER
    }
