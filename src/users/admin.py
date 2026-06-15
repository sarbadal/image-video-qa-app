from django.contrib import admin
from users.models import Profile, UserPreferences, EmailConfirmed


class UserNameColumnsMixin:
    @admin.display(ordering='user__first_name', description='First name')
    def first_name(self, obj):
        return obj.user.first_name

    @admin.display(ordering='user__last_name', description='Last name')
    def last_name(self, obj):
        return obj.user.last_name


@admin.register(Profile)
class ProfileAdmin(UserNameColumnsMixin, admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name')


@admin.register(UserPreferences)
class UserPreferencesAdmin(UserNameColumnsMixin, admin.ModelAdmin):
    list_display = (
        'user',
        'first_name',
        'last_name',
        'default_img_zoom',
        'default_img_threshold',
    )


@admin.register(EmailConfirmed)
class EmailConfirmedAdmin(UserNameColumnsMixin, admin.ModelAdmin):
    list_display = (
        'user',
        'first_name',
        'last_name',
        'activation_key',
        'email_confirmed',
        'approver_name',
    )

    @admin.display(description='Approver')
    def approver_name(self, obj):
        return obj.user.approver
