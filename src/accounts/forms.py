# coding=utf-8

from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()


EMAIL_INPUT_ATTRS = {
    'class': 'form-control',
    'type': 'email',
    'placeholder': 'Email address',
    'required': True,
}

PASSWORD_INPUT_ATTRS = {
    'class': 'form-control',
    'placeholder': 'Password',
    'required': True,
}


class UserCreationForm(forms.ModelForm):
    """Form for creating a new user account."""

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        """Model binding for account creation."""
        model = User
        fields = ['email', 'first_name', 'last_name']

    def clean_password2(self):
        """Ensure password confirmation matches the original password."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')

        return password2

    def save(self, commit=True):
        """Persist the user with a hashed password."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

        return user


class UserLoginForm(forms.Form):
    """Form for authenticating an existing user account."""

    query = forms.CharField(
        label='Email',
        widget=forms.TextInput(attrs=EMAIL_INPUT_ATTRS)
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs=PASSWORD_INPUT_ATTRS)
    )

    def clean(self):
        """Validate user existence and password correctness."""
        cleaned_data = super().clean()
        query = cleaned_data.get('query')
        password = cleaned_data.get('password')

        if not query or not password:
            return cleaned_data

        user_qs_final = User.objects.filter(email__iexact=query).distinct()

        if not user_qs_final.exists() or user_qs_final.count() != 1:
            raise forms.ValidationError('User does not exist')

        user_obj = user_qs_final.first()

        if not user_obj.check_password(password):
            raise forms.ValidationError('Credentials are not correct')
        cleaned_data['user_obj'] = user_obj

        return cleaned_data
