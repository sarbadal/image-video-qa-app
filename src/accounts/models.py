from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


APPROVER_CHOICES = [
    ('sarbadal.pal@annalect.com', 'Sarbadal Pal')
]


class CustomUserManager(BaseUserManager):
    """Custom User Manager"""

    def _normalize_user_fields(self, email, first_name, last_name):
        normalized_email = self.normalize_email(email).lower()
        normalized_first_name = first_name.title()
        normalized_last_name = last_name.title()
        return normalized_email, normalized_first_name, normalized_last_name

    def create_user(self, email, first_name, last_name, approver, password=None):
        """Override create_user method"""
        if not email:
            raise ValueError('Users must have an email address')

        email, first_name, last_name = self._normalize_user_fields(
            email,
            first_name,
            last_name,
        )

        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            approver=approver,
        )
        user.set_password(password)
        user.is_active = False
        user.save(using=self._db)

        return user

    def create_superuser(self, email, first_name, last_name, approver, password=None):
        """Override superuser method"""
        user = self.create_user(email, first_name, last_name, approver, password=password)
        user.is_admin = True
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)

        return user


class CustomUser(AbstractBaseUser):
    """Custom User"""
    email = models.EmailField(max_length=255, unique=True, verbose_name='email address')
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='First Name')
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Last Name')
    approver = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'approver']

    def __str__(self):
        return self.email

    def get_short_name(self):
        """
        The user is identified by
        their email address
        """
        return self.email

    def has_perm(self, perm, obj=None):
        """
        Does the user have a specific permission?

        Simplest possible answer: Yes, if admin user No otherwise
        """
        return self.is_admin

    def has_module_perms(self, app_label):
        """
        Does the user have permissions
        to view the app 'app_label'?

        Simplest possible answer: Yes, if admin user No otherwise
        """
        return self.is_admin

    class Meta:
        """Meta class"""
        verbose_name_plural = 'Custom Users'


class Approvers(models.Model):
    """Approver mappings for user approval flow."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    class Meta:
        """Meta class"""
        verbose_name_plural = 'Approvers'
