from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render


def health(request):
    """Lightweight health check for deployment monitoring."""
    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ok"})
    except Exception as exc:
        return JsonResponse({"status": "error", "detail": str(exc)}, status=503)


def home(request):
    features = [
        {
            "title": "Find Your Campus Circle",
            "text": "Meet classmates by interests, departments, clubs, and events.",
        },
        {
            "title": "Smart Matching",
            "text": "Discover study partners, project teammates, and social matches.",
        },
        {
            "title": "College-First Community",
            "text": "A focused space for students to connect beyond crowded group chats.",
        },
    ]
    return render(request, "core/home.html", {"features": features})
