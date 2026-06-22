from django.urls import path
from django.contrib.auth import views as auth_views
from accounts import views as account_views
from users import views
from users.forms import CustomPasswordResetForm, CustomSetPasswordForm

urlpatterns = [
    path('login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    # Keep legacy preference URL available after removing preference-specific view.
    path('preference/', views.profile, name='preference'),
    path(
        'email/confirmation/<str:activation_key>/',
        views.email_confirm,
        name='email_activation'
    ),
    path(
        'activation/confirmation/<str:activation_key>/',
        views.activate_user,
        name='user_activation'
    ),
    path('change-password/', views.change_password, name='change_password'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            form_class=CustomPasswordResetForm,
            template_name='registration/password_reset.html'
        ),
        name='password_reset'
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            form_class=CustomSetPasswordForm,
            template_name='registration/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),
]
