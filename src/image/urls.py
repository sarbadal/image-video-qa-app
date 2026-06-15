from django.urls import path
from image import views


app_name = 'image'

urlpatterns = [
    path('', views.process_files, name='image'),
    path('creative-img/image/<int:id>/', views.display_img, name='single-image'),
]