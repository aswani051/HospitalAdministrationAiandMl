import json
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .services import generate_chat_response
from .ml.recommender import recommend_department

logger = logging.getLogger(__name__)

# Keywords indicating patient is describing symptoms or seeking medical department guidance
SYMPTOM_INDICATORS = [
    "pain", "ache", "swell", "fever", "cough", "rash", "hurt", "fracture",
    "bleed", "dizzy", "headache", "migraine", "chest", "breath", "throat",
    "ear", "eye", "joint", "knee", "spine", "back", "stomach", "nausea",
    "vomit", "cramp", "period", "itch", "skin", "burn", "infant", "baby",
    "child", "toddler", "seizure", "numb", "tingling", "fatigue", "weakness",
    "symptom", "recommend", "department", "doctor", "consult", "sick", "ill"
]


def chatbot_page(request):
    """
    Renders page with AI Patient Assistant chatbot.
    """
    return render(request, "chatbot/chatbot.html")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def recommend_department_api(request):
    """
    Dedicated API endpoint for AI Department Recommendations.
    Accepts:
        POST: JSON body `{"symptoms": "..."}` or form-data `symptoms=...`
        GET: Query parameter `?symptoms=...`
    Returns:
        JSON response with predicted department, confidence score, SQLite database mapping,
        appointment booking URL, emergency safety alerts, and medical disclaimer.
    """
    try:
        symptoms = ""

        if request.method == "POST":
            if request.content_type and "application/json" in request.content_type:
                try:
                    data = json.loads(request.body.decode("utf-8") if isinstance(request.body, bytes) else request.body)
                    symptoms = data.get("symptoms") or data.get("message") or ""
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return JsonResponse({
                        "success": False,
                        "error": "Invalid JSON format in request body."
                    }, status=400)
            else:
                symptoms = request.POST.get("symptoms") or request.POST.get("message") or ""
        else:
            symptoms = request.GET.get("symptoms") or request.GET.get("q") or ""

        symptoms = symptoms.strip()

        if not symptoms:
            return JsonResponse({
                "success": False,
                "error": "Please describe your symptoms to receive an AI department recommendation.",
                "code": "EMPTY_INPUT"
            }, status=400)

        result = recommend_department(symptoms)
        status_code = 200 if result.get("success") else 400

        return JsonResponse(result, status=status_code)

    except Exception as e:
        logger.exception("Error in recommend_department_api: %s", e)
        return JsonResponse({
            "success": False,
            "error": "An error occurred while evaluating your symptoms. Please try again.",
            "details": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """
    Unified Chatbot API endpoint.
    Automatically classifies patient input:
    - If symptoms or clinical concerns are described, runs the Scikit-learn ML model
      and returns the department recommendation with the booking button.
    - If general questions (hospital hours, location, services) are asked,
      returns conversational guidance.
    """
    try:
        if not request.body:
            return JsonResponse({
                "success": False,
                "error": "Request body cannot be empty."
            }, status=400)

        try:
            data = json.loads(request.body.decode("utf-8") if isinstance(request.body, bytes) else request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({
                "success": False,
                "error": "Invalid JSON format."
            }, status=400)

        message = data.get("message", "").strip()

        if not message:
            return JsonResponse({
                "success": False,
                "error": "Message cannot be empty."
            }, status=400)

        lower_msg = message.lower()

        # Check if the message contains symptom or clinical keywords
        has_symptoms = any(keyword in lower_msg for keyword in SYMPTOM_INDICATORS)

        if has_symptoms or len(message.split()) >= 3:
            # Run Scikit-learn recommendation engine
            rec_result = recommend_department(message)
            if rec_result.get("success"):
                return JsonResponse({
                    "success": True,
                    "is_recommendation": True,
                    "recommendation": rec_result
                })

        # Fallback to conversational response for general questions
        response = generate_chat_response(message)
        return JsonResponse({
            "success": True,
            "is_recommendation": False,
            "response": response
        })

    except Exception as e:
        logger.exception("Chat API error: %s", e)
        return JsonResponse({
            "success": False,
            "error": "Unable to process your request at this time."
        }, status=500)
