from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path("", views.page("camera"), name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="web/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("api/token/", views.api_token, name="api_token"),
    path("gestures/", views.page("gestures"), name="gestures"),
    path("gestures/new/", views.page("upload"), name="upload"),
    path("library/", views.page("library"), name="library"),
    path("training/", views.page("training"), name="training"),
    path("models/", views.page("models"), name="models"),
    path("camera/", views.page("camera"), name="camera"),
]
