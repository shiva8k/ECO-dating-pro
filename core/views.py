from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from accounts.models import Profile


def health(request):
    """Lightweight health check for deployment monitoring."""
    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ok"})
    except Exception as exc:
        return JsonResponse({"status": "error", "detail": str(exc)}, status=503)


def home(request):
    featured_profiles = Profile.objects.exclude(
        profile_picture=""
    )[:4]

    return render(request, "core/home.html", {
        "featured_profiles": featured_profiles
    })