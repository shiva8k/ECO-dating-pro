from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve

ONBOARDING_EXEMPT_URL_NAMES = {
    "onboarding",
    "logout",
    "login",
    "signup",
    "admin:index",
}


class OnboardingRequiredMiddleware:
    """Redirect authenticated users to onboarding until their profile is complete."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and not request.path.startswith("/admin/")
            and not request.path.startswith(settings.MEDIA_URL)
        ):
            try:
                url_name = resolve(request.path_info).url_name
            except Exception:
                url_name = None

            if url_name not in ONBOARDING_EXEMPT_URL_NAMES:
                profile = getattr(request.user, "profile", None)
                if profile is None:
                    from .models import Profile

                    profile, _ = Profile.objects.get_or_create(user=request.user)

                if profile.needs_onboarding():
                    return redirect("onboarding")

        return self.get_response(request)
