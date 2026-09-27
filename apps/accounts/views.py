import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods


@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


@require_http_methods(["POST"])
def login_view(request):
    try:
        body = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        body = {}
    username = body.get("username") or request.POST.get("username", "")
    password = body.get("password") or request.POST.get("password", "")
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"detail": "Invalid username or password."}, status=400)
    login(request, user)
    profile = getattr(user, "profile", None)
    return JsonResponse(
        {
            "id": user.id,
            "username": user.username,
            "role": profile.role if profile else "designer",
        }
    )


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return JsonResponse({"ok": True})


@ensure_csrf_cookie
@require_http_methods(["GET"])
def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=401)
    profile = getattr(request.user, "profile", None)
    return JsonResponse(
        {
            "authenticated": True,
            "id": request.user.id,
            "username": request.user.username,
            "role": profile.role if profile else "designer",
        }
    )
