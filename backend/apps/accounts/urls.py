from django.urls import path

from . import views

urlpatterns = [
    path("token/", views.obtain_token, name="auth-token"),
    path("login/", views.login_view, name="auth-login"),
    path("logout/", views.logout_view, name="auth-logout"),
    path("me/", views.me, name="auth-me"),
    path("register/", views.register, name="auth-register"),
]
