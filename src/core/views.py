from django.shortcuts import render
from users.models import UserPreferences


def landing_page(request):
    user_preference = None
    if request.user.is_authenticated:
        user_preference = UserPreferences.objects.filter(user=request.user).only('home').first()

    context = {
        'home': user_preference.home if user_preference else None,
    }
    return render(request, 'landing_page.html', context)
    