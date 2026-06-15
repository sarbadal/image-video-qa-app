from django import forms


VIDEO_INPUT_ATTRS = {
    'multiple': True,
    'accept': 'video/*',
}


class VideoFieldForm(forms.Form):
    """Form for uploading one or more video files."""

    file_field = forms.FileField(
        widget=forms.ClearableFileInput(attrs=VIDEO_INPUT_ATTRS)
    )