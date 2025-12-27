import json
from django.http import JsonResponse
from django.shortcuts import render

from .utils import ask_vocatus
from .models import AIRequestLog


# Create your views here.

def vocatus_chat(request):
    """
    Ontvangt een chatbericht en geeft AI-antwoord terug als JSON.
    """

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST required"},
            status=400
        )

    try:
        data = json.loads(request.body)
        user_input = data.get("message", "")
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400
        )

    if not user_input:
        return JsonResponse(
            {"error": "Empty message"},
            status=400
        )

    answer, messages, cost_info = ask_vocatus(user_input)
    
    # zorg dat de sessie een key heeft
    if not request.session.session_key:
        request.session.create()

    AIRequestLog.objects.create(
        user=None,
        session_key=request.session.session_key,
        input_tokens=cost_info["input_tokens"],
        output_tokens=cost_info["output_tokens"],
        request_cost=cost_info["request_cost"],
    )

    return JsonResponse({
        "answer": answer,
        "cost": cost_info
    })



def chat_page(request):
    return render(request, "bierguru/chat.html")





