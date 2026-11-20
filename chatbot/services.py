import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize Gemini client safely
client = None
if getattr(settings, "GEMINI_API_KEY", None):
    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        logger.warning("Could not initialize Google GenAI Client: %s", e)

MODEL_NAME = "gemini-2.5-flash-lite"


def generate_chat_response(user_message):
    """
    Generates conversational response for general hospital questions.
    Falls back gracefully if API key is not configured or network issues arise.
    """
    if not client:
        return (
            "👋 Welcome to Aswani Hospital! I am your AI Patient Assistant. "
            "You can describe your symptoms, and I will recommend the right hospital "
            "department (General Medicine, Orthopaedics, Cardiology, Dermatology, Neurology, "
            "ENT, Paediatrics, or Gynaecology) and help you book an appointment with our specialist doctors."
        )

    prompt = f"""
You are the AI Patient Assistant for Aswani Hospital.

Your responsibilities:
- Explain hospital departments.
- Provide doctor and department information.
- Guide patients about appointments.
- Answer general hospital questions.
- Provide basic symptom-based department guidance.

Safety rules:
- Never diagnose diseases.
- Never prescribe medicines or dosages.
- Never replace professional medical advice.
- For emergencies, advise immediate medical attention.
- Do not invent hospital information.

Patient message:
{user_message}

Provide a simple, friendly and helpful response.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        if response and response.text:
            return response.text.strip()

        logger.warning("Gemini returned an empty response.")
        return "I'm here to assist you with Aswani Hospital services. How can I help you today?"

    except Exception as e:
        error_code = getattr(e, "code", None)
        error_message = str(e).upper()
        logger.exception("Gemini API request failed. Code: %s", error_code)

        if error_code == 429 or "429" in error_message:
            return "Our AI assistant is currently receiving high demand. Please try again in a few moments."

        return (
            "Welcome to Aswani Hospital. You can use our Symptom Checker to find the right department "
            "or contact our helpdesk at +91 98765 43210 for appointment assistance."
        )
