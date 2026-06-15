import hashlib
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from accounts.models import CustomUser


def validate_rgb(value):
    if value < 0 or value > 255:
        raise ValidationError(f'{value} must be between 0 and 255')


def generate_activation_key(email):
    timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    payload = f'{email}-{timestamp}'.encode()
    return hashlib.sha224(payload).hexdigest()


class Profile(models.Model):
    """User Profile model"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    profile_image = models.ImageField(
        default='default.jpg',
        upload_to='profileLogo', 
        verbose_name='Upload profile pic',
        null=False, blank=False
    )

    def __str__(self):
        return f'User - {self.user.email}'

    def delete(self, *args, **kwargs):
        if self.profile_image and self.profile_image.name != 'default.jpg':
            self.profile_image.delete(save=False)
        super().delete(*args, **kwargs)

    class Meta:
        """Meta class"""
        verbose_name_plural = 'User Profile'


class UserPreferences(models.Model):
    """User preferences for image display"""
    HOME_CHOICES = [
        ('IMAGE', 'IMAGE'),
        ('VIDEO', 'VIDEO')
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    home = models.CharField(max_length=10, choices=HOME_CHOICES, default='IMAGE', verbose_name='home')
    default_img_zoom = models.IntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(500)])
    default_video_zoom = models.IntegerField(default=225, validators=[MinValueValidator(0), MaxValueValidator(500)])
    default_img_threshold = models.IntegerField(default=150, validators=[MinValueValidator(0), MaxValueValidator(255)])
    default_video_threshold = models.IntegerField(default=15, validators=[MinValueValidator(0), MaxValueValidator(255)])
    default_tbl_color_r = models.IntegerField(default=250, validators=[validate_rgb])
    default_tbl_color_g = models.IntegerField(default=250, validators=[validate_rgb])
    default_tbl_color_b = models.IntegerField(default=250, validators=[validate_rgb])

    def __str__(self):
        return f'User - {self.user.email}'

    class Meta:
        """Meta class"""
        verbose_name_plural = 'User Preferences'
    

class EmailConfirmed(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    activation_key = models.CharField(max_length=500)
    email_confirmed = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    class Meta:
        """Meta class"""
        verbose_name_plural = 'User Email-Confirmed'


@receiver(post_save, sender=CustomUser)
def create_user_defaults(sender, instance, created, **kwargs):
    """Create default one-to-one records when a user is created."""
    if created:
        Profile.objects.create(user=instance)
        UserPreferences.objects.create(user=instance)
        EmailConfirmed.objects.create(
            user=instance,
            activation_key=generate_activation_key(instance.email),
        )
