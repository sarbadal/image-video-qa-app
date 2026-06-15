from django.apps import AppConfig


class VideoConfig(AppConfig):
    """Configuration for the video app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video'
    verbose_name = 'Video'
