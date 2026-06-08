from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import RegistrationForm
from .tokens import create_access_token


def avatar_url(user):
    try:
        avatar = user.profile.avatar
    except AttributeError:
        avatar = "avatar1.png"
    return f"/static/images/{avatar}"


def page(name):
    @login_required
    def render_page(request):
        return render(request, f"web/{name}.html", {
            "backend_url": settings.BACKEND_URL,
            "avatar_url": avatar_url(request.user),
        })

    return render_page


def register(request):
    if request.user.is_authenticated:
        return redirect("/")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("/")
    return render(request, "web/register.html", {"form": form, "backend_url": settings.BACKEND_URL})


@login_required
@require_POST
def api_token(request):
    return JsonResponse({"token": create_access_token(request.user.pk)})
