# coding=utf-8
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.models import Group
from accounts.models import CustomUser, Approvers
from accounts.forms import UserCreationForm

admin.site.unregister(Group)
admin.site.site_header = 'Creative QA App Admin'


@admin.register(CustomUser)
class UserAdmin(ImportExportModelAdmin):
    """Admin configuration for custom users."""

    add_form = UserCreationForm

    list_display = (
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_admin',
        'is_staff',
        'approver'
    )
    list_filter = ('is_admin',)
    fieldsets = (
        (
            None, {
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'is_active',
                    'is_staff',
                    'approver',
                    'password'
                )
            }
        ),
        ('Permissions', {
            'fields': ('is_admin',)
        })
    )
    add_fieldsets = (
        (
            None, {
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'is_active',
                    'is_staff',
                    'approver',
                    'password'
                )
            }
        ),
        ('Permissions', {
            'fields': ('is_admin',)
        })
    )

    search_fields = ('email',)
    ordering = ('email',)

    filter_horizontal = ()


class UserNameColumnsMixin:
    @admin.display(ordering='user__first_name', description='First name')
    def first_name(self, obj):
        return obj.user.first_name

    @admin.display(ordering='user__last_name', description='Last name')
    def last_name(self, obj):
        return obj.user.last_name


@admin.register(Approvers)
class ApproverAdmin(UserNameColumnsMixin, ImportExportModelAdmin):
    """Admin configuration for approver mappings."""

    list_display = ('user', 'first_name', 'last_name')
    list_select_related = ('user',)
