import re
from django.db import models
from accounts.models import CustomUser


def video_file_path(instance, filename):
    filename = filename.replace(' ', '').strip()
    filename = re.sub(r'(?u)[^-\w. ]', '', filename)
    return 'video/user_{0}/{1}'.format(instance.user.id, filename)


class VideoRecordBase(models.Model):
    """Shared metadata fields for video records."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    size = models.CharField(max_length=150)
    video_type = models.CharField(max_length=25)
    video_width = models.IntegerField(default=0)
    video_height = models.IntegerField(default=0)
    resolution = models.CharField(max_length=150)
    aspect_ratio = models.CharField(max_length=150)
    video_fps = models.CharField(max_length=20)
    video_bit_rate = models.CharField(max_length=150)
    audio_bit_rate = models.CharField(max_length=150)
    audio_sample_rate = models.CharField(max_length=150)
    max_audio_decibel = models.CharField(max_length=150)
    video_codec = models.CharField(max_length=150)
    audio_codec = models.CharField(max_length=150)
    duration = models.CharField(max_length=150)
    name_width = models.IntegerField(default=0)
    name_height = models.IntegerField(default=0)
    upload_instance = models.IntegerField(default=0)
    sl_no = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class VideoTable(VideoRecordBase):
    """Video metadata with uploaded video source file."""

    video_src = models.FileField(upload_to=video_file_path, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Video Table'

    def delete(self, *args, **kwargs):
        if self.video_src:
            self.video_src.delete(save=False)
        super().delete(*args, **kwargs)


class VideoTableMetaData(VideoRecordBase):
    """Video metadata-only record."""

    class Meta:
        verbose_name_plural = 'Video Table Metadata'


class VideoAspectRatio(models.Model):
    """User preferences for Video QA"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    width = models.IntegerField()
    height = models.IntegerField()

    def __str__(self):
        return f'User - {self.user.email}'

    class Meta:
        """Meta class"""
        verbose_name_plural = 'Aspect Ratios'


class VideoFormats(models.Model):
    """User defined acceptable Video Formats"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    formats = models.CharField(max_length=50, blank=False, null=False)

    def __str__(self):
        return f'User - {self.user.email}'

    class Meta:
        """Meta class"""
        verbose_name_plural = 'Video Formats'


class VideoDurations(models.Model):
    """User defined acceptable Video Formats"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    durations = models.IntegerField(blank=False, null=False)

    def __str__(self):
        return f'User - {self.user.email}'

    class Meta:
        """Meta class"""
        verbose_name_plural = 'Video Duraions'


class AudioDecibel(models.Model):
    """User defined acceptable Video Formats"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    max_decibel = models.IntegerField(blank=False, null=False)
    min_decibel = models.IntegerField(blank=False, null=False)
    
    def __str__(self):
        return f'User - {self.user.email}'

    class Meta:
        """Meta class"""
        verbose_name_plural = 'Video Decibel'
