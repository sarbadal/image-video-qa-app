from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from video.models import (
    VideoTable,
    VideoTableMetaData,
    VideoAspectRatio,
    VideoFormats,
    VideoDurations,
    AudioDecibel
)


class UserNameColumnsMixin:
    @admin.display(ordering='user__first_name', description='First name')
    def first_name(self, obj):
        return obj.user.first_name

    @admin.display(ordering='user__last_name', description='Last name')
    def last_name(self, obj):
        return obj.user.last_name


@admin.register(VideoTable, VideoTableMetaData)
class VideoTableAdmin(UserNameColumnsMixin, ImportExportModelAdmin):
    """Admin configuration for video table models."""

    list_display = ('user', 'name', 'first_name', 'last_name')
    list_select_related = ('user',)


@admin.register(VideoAspectRatio)
class VideoAspectRatioAdmin(UserNameColumnsMixin, admin.ModelAdmin):
    """Admin configuration for user video aspect ratios."""

    list_display = ('user', 'first_name', 'last_name', 'width', 'height')
    list_select_related = ('user',)


@admin.register(VideoFormats)
class VideoFormatsAdmin(UserNameColumnsMixin, admin.ModelAdmin):
    """Admin configuration for user video format preferences."""

    list_display = ('user', 'first_name', 'last_name', 'formats')
    list_select_related = ('user',)


@admin.register(VideoDurations)
class VideoDurationsAdmin(UserNameColumnsMixin, admin.ModelAdmin):
    """Admin configuration for user video duration preferences."""

    list_display = ('user', 'first_name', 'last_name', 'durations')
    list_select_related = ('user',)


@admin.register(AudioDecibel)
class AudioDecibelAdmin(UserNameColumnsMixin, admin.ModelAdmin):
    """Admin configuration for user audio decibel preferences."""

    list_display = ('user', 'first_name', 'last_name', 'max_decibel', 'min_decibel')
    list_select_related = ('user',)
