from django.urls import path

from . import views

app_name = "authentication"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("login/sso/", views.sso_login, name="sso_login"),
    path("login/sso/callback/", views.sso_callback, name="sso_callback"),
]