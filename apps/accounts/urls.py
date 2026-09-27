from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.csrf, name="csrf"),
    path("login/", views.login_view, name="api_login"),
    path("logout/", views.logout_view, name="api_logout"),
    path("me/", views.me, name="me"),
]
