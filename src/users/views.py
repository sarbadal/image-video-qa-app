from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.forms import inlineformset_factory
from accounts.models import CustomUser
from users.forms import (
    UserRegisterForm,
    UserPasswordChangeForm,
    UserUpdateForm,
    ProfileUpdateForm,
    UserPreferencesForm
)
from users.models import Profile, EmailConfirmed, UserPreferences
from video.models import VideoAspectRatio, VideoFormats, VideoDurations, AudioDecibel


def _build_aspect_ratio_formset():
    return inlineformset_factory(
        CustomUser,
        VideoAspectRatio,
        fields=['width', 'height'],
        can_delete=True,
        extra=1,
    )


def _build_video_format_formset():
    return inlineformset_factory(
        CustomUser,
        VideoFormats,
        fields=['formats'],
        can_delete=True,
        extra=1,
    )


def _build_video_duration_formset():
    return inlineformset_factory(
        CustomUser,
        VideoDurations,
        fields=['durations'],
        can_delete=True,
        extra=1,
    )


def _build_audio_decibel_formset():
    return inlineformset_factory(
        CustomUser,
        AudioDecibel,
        fields=['max_decibel', 'min_decibel'],
        can_delete=False,
        extra=1,
        max_num=1,
    )


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
    """Docstring"""
    config = get_object_or_404(UserPreferences, user=request.user)

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
            'home': config.home,
            'avatar': Profile.objects.get(user=request.user).profile_image,
            'title': 'Change Password'
        }
    )


@login_required
def preference(request):
    """doc string"""
    avatar = get_object_or_404(Profile, user=request.user)
    f_name = f'{avatar.user.first_name} {avatar.user.last_name}'

    config = get_object_or_404(UserPreferences, user=request.user)
    form = UserPreferencesForm(instance=config)

    aspect_ratio_formset = _build_aspect_ratio_formset()(instance=request.user)
    video_format_formset = _build_video_format_formset()(instance=request.user)
    video_duration_formset = _build_video_duration_formset()(instance=request.user)
    audio_db_formset = _build_audio_decibel_formset()(instance=request.user)

    if request.method == 'POST':
        p_form = UserPreferencesForm(request.POST, instance=request.user.userpreferences)

        if p_form.is_valid():
            p_form.save()
            return redirect('preference')

    context = {
        'avatar': avatar.profile_image,
        'name': f_name,
        'form': form,
        'aspect_ratio_formset': aspect_ratio_formset,
        'video_format_formset': video_format_formset,
        'video_duration_formset': video_duration_formset,
        'audio_db_formset': audio_db_formset,
        'home': config.home,
        'r': config.default_tbl_color_r,
        'g': config.default_tbl_color_g,
        'b': config.default_tbl_color_b
    }

    return render(request, 'users/preference.html', context)


@login_required
def video_aspect_ratio(request):
    """doc string"""
    user = request.user
    aspect_ratio_form = _build_aspect_ratio_formset()

    if request.method == 'POST':
        form = aspect_ratio_form(request.POST, instance=user)

        if form.is_valid():
            form.save()
            return redirect('preference')

    return redirect('preference')


@login_required
def video_duration(request):
    """doc string"""
    user = request.user
    video_duration_form = _build_video_duration_formset()

    if request.method == 'POST':
        form = video_duration_form(request.POST, instance=user)

        if form.is_valid():
            form.save()
            return redirect('preference')

    return redirect('preference')


@login_required
def video_format(request):
    """doc string"""
    user = request.user
    video_format_form = _build_video_format_formset()

    if request.method == 'POST':
        form = video_format_form(request.POST, instance=user)

        if form.is_valid():
            form.save()
            return redirect('preference')

    return redirect('preference')


@login_required
def audio_db_minmax(request):
    """doc string"""
    user = request.user
    audio_decibel_form = _build_audio_decibel_formset()

    if request.method == 'POST':
        form = audio_decibel_form(request.POST, instance=user)

        if form.is_valid():
            form.save()
            return redirect('preference')

    return redirect('preference')


@login_required
def profile(request):
    """doc string"""
    user = request.user
    config = get_object_or_404(UserPreferences, user=request.user)

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
        'home': config.home,
        'avatar': Profile.objects.get(user=request.user).profile_image,
        'title': 'Profile',
    }

    return render(request, 'users/profile.html', context)
