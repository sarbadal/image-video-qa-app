from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.http import HttpRequest, HttpResponse

from accounts.forms import UserLoginForm


def login_view(request: HttpRequest) -> HttpResponse:
    """Authenticate a user and redirect to the preferred landing page."""
    form = UserLoginForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user_obj = form.cleaned_data.get('user_obj')
            login(request, user_obj)

            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)

            home = 'image'

            if home == 'image':
                return redirect('image')

            return redirect('image')

    return render(
        request,
        'users/login.html',
        {'form': form, 'title': 'Login'}
    )


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log out the current user and redirect to the login page."""
    logout(request)
    return redirect("login")
