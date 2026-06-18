from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from typing import Optional, Tuple


APPROVER_CHOICES: list[tuple[str, str]] = [
    ('sarbadal.pal@annalect.com', 'Sarbadal Pal')
]


class CustomUser(AbstractBaseUser):
    """Application user model authenticated via email address."""
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

    def __str__(self) -> str:
        """Return the canonical string representation for the user."""
        return self.email

    def get_short_name(self) -> str:
        """Return the compact user identifier shown in admin contexts."""
        return self.email

    def has_perm(self, perm: str, obj: object = None) -> bool:
        """Return admin-based permission status for a specific permission."""
        return self.is_admin

    def has_module_perms(self, app_label: str) -> bool:
        """Return whether the user can access the given app module."""
        return self.is_admin

    class Meta:
        """Meta class"""
        verbose_name_plural = 'Custom Users'


class Approvers(models.Model):
    """Approver mappings for user approval flow."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Return the related user email for display purposes."""
        return self.user.email

    class Meta:
        """Meta class"""
        verbose_name_plural = 'Approvers'


class CustomUserManager(BaseUserManager):
    """Manager for creating normalized application users and superusers."""

    def _normalize_user_fields(self, email: str, first_name: str, last_name: str) -> Tuple[str, str, str]:
        """Normalize and format email and name fields before persistence."""
        normalized_email = self.normalize_email(email).lower()
        normalized_first_name = first_name.title()
        normalized_last_name = last_name.title()
        return normalized_email, normalized_first_name, normalized_last_name

    def create_user(self, email: str, first_name: str, last_name: str, approver: str, password: Optional[str] = None) -> CustomUser:
        """Create an inactive user with normalized identity fields."""
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

    def create_superuser(self, email: str, first_name: str, last_name: str, approver: str, password: Optional[str] = None) -> CustomUser:
        """Create an active staff/admin user with elevated permissions."""
        user = self.create_user(email, first_name, last_name, approver, password=password)
        user.is_admin = True
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)

        return user
