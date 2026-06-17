from django.urls import path
from video.views import process_video

urlpatterns = [
    path('', process_video, name='video'),
]