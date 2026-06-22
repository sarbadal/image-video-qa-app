from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from accounts.models import CustomUser
from users.forms import (
    UserRegisterForm,
    UserPasswordChangeForm,
    UserUpdateForm,
    ProfileUpdateForm,
)
from users.models import Profile, EmailConfirmed


def _get_home_preference(user):
    """Return user's home preference when available, otherwise None."""
    preference = getattr(user, 'userpreferences', None)
    return getattr(preference, 'home', None)


def register(request):
    """User registration view"""

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)

            email = instance.email.lower()
            first_name = instance.first_name.title()
            last_name = instance.last_name.title()
            approver = instance.approver

            instance.email = email
            instance.first_name = first_name
            instance.last_name = last_name
            instance.approver = approver
            instance.is_active = False

            instance.save()

            # send user email and inform that status
            user = EmailConfirmed.objects.get(user=instance)
            site = get_current_site(request)
            message_html = render_to_string(
                'users/verify_email.html',
                {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'domain': site.domain,
                    'activation_key': user.activation_key
                }
            )
            send_mail(
                'Email Confirmation',
                message_html,
                'no-reply@annalect.com',
                [email],
                fail_silently=True
            )

            return render(request, 'users/registration_start.html')
    else:
        form = UserRegisterForm()

    return render(
        request,
        'users/register.html',
        {
            'form': form,
            'title': 'Registration'
        }
    )


def email_confirm(request, activation_key):
    """activate user account through email"""
    email_confirmation = get_object_or_404(
        EmailConfirmed.objects.select_related('user'),
        activation_key=activation_key,
    )
    requester_user = email_confirmation.user

    if email_confirmation.email_confirmed:
        context = {
            'verified_email': requester_user.email,
            'title': 'Email Verification'
        }
        return render(
            request, 'users/email_already_confirmed.html', context
        )

    requester = requester_user.email

    email_confirmation.email_confirmed = True
    email_confirmation.save()

    # send user email to the approver
    approver_email = requester_user.approver
    approver_instance = get_object_or_404(CustomUser, email=approver_email)

    first_name = approver_instance.first_name
    last_name = approver_instance.last_name

    site = get_current_site(request)
    message_html = render_to_string(
        'users/activate_user.html',
        {
            'first_name': first_name,
            'last_name': last_name,
            'approver': approver_email,
            'requester': requester,
            'domain': site.domain,
            'activation_key': email_confirmation.activation_key
        }
    )
    send_mail(
        'Approval Request for Creative QA App',
        message_html,
        'no-reply@annalect.com',
        [approver_email],
        fail_silently=True
    )

    return render(request, 'users/email_confirmed.html')


@login_required
def activate_user(request, activation_key):
    """activate user account through email"""
    confirmation = get_object_or_404(
        EmailConfirmed.objects.select_related('user'),
        activation_key=activation_key,
    )
    requester = confirmation.user

    if confirmation.email_confirmed:
        login_user_email = request.user.email
        approver_email = requester.approver

        if approver_email and login_user_email.lower() == approver_email.lower():
            requester.is_active = True
            requester.save()

            # send user email and inform that status
            site = get_current_site(request)
            message_html = render_to_string(
                'users/approval_notification_user.html',
                {
                    'first_name': requester.first_name,
                    'last_name': requester.last_name,
                    'email': requester.email,
                    'domain': site.domain
                }
            )
            send_mail(
                'Request Approved',
                message_html,
                'no-reply@annalect.com',
                [requester.email],
                fail_silently=True
            )

            context = {
                'activated_email': requester.email,
                'title': 'Activation',
                'avatar': Profile.objects.get(user=request.user).profile_image
            }

            return render(request, 'users/access_approved.html', context)

        else:
            return render(request, 'users/user_activation_unknown_auth.html')

    else:
        unverified_email = requester.email
        return render(
            request,
            'users/email_not_confirmed.html',
            {
                'unverified_email': unverified_email
            }
        )


@login_required
def change_password(request):
    """Change password view for authenticated users."""
    if request.method == 'POST':
        form = UserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(
                request,
                'Your password has been successfully updated!'
            )

            return redirect('change_password')

        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = UserPasswordChangeForm(request.user)

    return render(
        request,
        'users/change_password.html',
        {
            'form': form,
            'home': _get_home_preference(request.user),
            'avatar': Profile.objects.get(user=request.user).profile_image,
            'title': 'Change Password'
        }
    )


@login_required
def profile(request):
    """View for updating user profile information."""
    user = request.user

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your account has been updated!')

            return redirect('profile')

        return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'user': user,
        'home': _get_home_preference(request.user),
        'avatar': Profile.objects.get(user=request.user).profile_image,
        'title': 'Profile',
    }

    return render(request, 'users/profile.html', context)
