from django import forms
from accounts.models import CustomUser, Approvers
from django.contrib.auth.forms import (
    UserCreationForm, 
    PasswordChangeForm, 
    PasswordResetForm, 
    SetPasswordForm
)
from users.models import Profile, UserPreferences

_APPROVED_EMAIL_DOMAINS = ['annalect.com', 'omc.com', 'gmail.com', 'yahoo.com', 'outlook.com']


def build_range_widget(min_value, max_value, step=1, include_width=True):
    attrs = {
        'class': 'custom-range',
        'type': 'range',
        'min': min_value,
        'max': max_value,
        'step': step,
    }
    if include_width:
        attrs['width'] = '100%'
    return forms.TextInput(attrs=attrs)


class UserRegisterForm(UserCreationForm):
    """Registration form for creating a new user."""
    email = forms.EmailField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'type': 'email',
                'placeholder': 'Email address'
            }
        )
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }
        )
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }
        )
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Create password'
            }
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Repeat password'
            }
        )
    )

    approver = forms.ModelChoiceField(
        queryset=Approvers.objects.all().distinct(),
        to_field_name='user',
        empty_label="Select Approver",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        """Model configuration for user registration."""
        model = CustomUser
        fields = [
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2',
            'approver'
        ]

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        domain = email.rsplit('@', maxsplit=1)[-1]

        if domain not in _APPROVED_EMAIL_DOMAINS:
            raise forms.ValidationError(
                f'Domain must be one of {_APPROVED_EMAIL_DOMAINS}', 
                code='email_domain'
            )

        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Email is already taken', 
                code='duplicate_email'
            )

        return email


class CustomPasswordResetForm(PasswordResetForm):
    """Password reset form with bootstrap-friendly input styling."""
    email = forms.EmailField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'type': 'email',
                'placeholder': 'Your registered e-mail...'
            }
        )
    )


class CustomSetPasswordForm(SetPasswordForm):
    """Form for setting a new password."""
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'New password'
            }
        )
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'New password confirmation'
            }
        )
    )


class UserPasswordChangeForm(PasswordChangeForm):
    """Form for changing an existing user password."""
    old_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Old Password'
            }
        )
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'New Password'
            }
        )
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'New Password Confirmation'
            }
        )
    )


class UserUpdateForm(forms.ModelForm):
    """Form for updating user profile details."""

    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control'
            }
        )
    )

    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control'
            }
        )
    )

    class Meta:
        """Model configuration for user updates."""
        model = CustomUser
        fields = ['first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating the user profile image."""

    profile_image = forms.ImageField(required=False, widget=forms.FileInput)

    class Meta:
        """Model configuration for profile image updates."""
        model = Profile
        fields = ['profile_image']


class UserPreferencesForm(forms.ModelForm):
    """Form for updating image/video display preferences."""

    default_tbl_color_r = forms.IntegerField(min_value=0, max_value=255, widget=build_range_widget(0, 255))
    default_tbl_color_g = forms.IntegerField(min_value=0, max_value=255, widget=build_range_widget(0, 255))
    default_tbl_color_b = forms.IntegerField(min_value=0, max_value=255, widget=build_range_widget(0, 255))

    default_img_threshold = forms.IntegerField(min_value=0, max_value=255, widget=build_range_widget(0, 255))
    default_video_threshold = forms.IntegerField(min_value=0, max_value=255, widget=build_range_widget(0, 255))

    default_img_zoom = forms.IntegerField(min_value=0, max_value=500, widget=build_range_widget(0, 500, step=5, include_width=False))
    default_video_zoom = forms.IntegerField(min_value=0, max_value=500, widget=build_range_widget(0, 500, step=5, include_width=False))

    HOME_CHOICES = (('IMAGE', 'Image'), ('VIDEO', 'Video'))
    home = forms.ChoiceField(
        label='Set Default Home',
        choices=HOME_CHOICES,
        widget=forms.RadioSelect,
    )
    
    class Meta:
        """Model configuration for user preferences."""
        model = UserPreferences
        fields = [
            'default_tbl_color_r',
            'default_tbl_color_g',
            'default_tbl_color_b',
            'default_img_threshold',
            'default_video_threshold',
            'default_img_zoom',
            'default_video_zoom',
            'home'
        ]


class AspectRatioForm(forms.ModelForm):
    """Simple form for width and height inputs."""

    w = forms.CharField(
        label='Width',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Width here'
        })
    )
    
    h = forms.CharField(
        label='Height',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Height here'
        })
    )


# AspectRatioCollectionFormSet = inlineformset_factory(
#     CustomUser, AspectRatioForm,
#     fields=('w', 'h'),
#     can_delete=True,
#     extra=1
# )