from django.shortcuts import redirect
from django.views.generic import TemplateView


class SpaView(TemplateView):
    template_name = "spa.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.conf import settings

        ctx["debug"] = settings.DEBUG
        return ctx


class LoginPageView(TemplateView):
    template_name = "login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("spa")
        return super().dispatch(request, *args, **kwargs)
