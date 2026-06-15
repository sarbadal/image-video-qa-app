from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from image.models import ImageTable, ImageTableMetaData


class UserNameColumnsMixin:
    @admin.display(ordering='user__first_name', description='First name')
    def first_name(self, obj):
        return obj.user.first_name

    @admin.display(ordering='user__last_name', description='Last name')
    def last_name(self, obj):
        return obj.user.last_name


@admin.register(ImageTable, ImageTableMetaData)
class ImageAdmin(UserNameColumnsMixin, ImportExportModelAdmin):
    """Admin configuration for image models."""

    list_display = (
        'user',
        'name',
        'img_type',
        'size_kb',
        'first_name',
        'last_name',
        'date_added',
    )
    list_select_related = ('user',)
