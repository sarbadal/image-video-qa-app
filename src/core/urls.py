from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from core.views import landing_page


app_urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url=f'{settings.STATIC_URL}favicon/favicon.ico', permanent=True)),
    path('', landing_page, name='landing_page'),
    path('image/', include('image.urls')),
    path('user/', include('users.urls')),
    path('admin/', admin.site.urls),
]


urlpatterns = [*app_urlpatterns]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
