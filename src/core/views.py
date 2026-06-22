from django.shortcuts import render


def landing_page(request):
    user_preference = None

    context = {
        'home': user_preference.home if user_preference else None,
    }
    return render(request, 'landing_page.html', context)
    