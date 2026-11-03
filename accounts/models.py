from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', CustomUser.Roles.SYSTEM_ADMIN)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None  # Remove default username; login with email
    email = models.EmailField(unique=True)

    class Roles(models.TextChoices):
        SYSTEM_ADMIN = 'SYSTEM_ADMIN', 'System Admin'
        TENANT_ADMIN = 'TENANT_ADMIN', 'Tenant Admin / Company Owner'
        DISPATCHER   = 'DISPATCHER',   'Dispatcher'
        DRIVER       = 'DRIVER',       'Fleet Driver'
        CUSTOMER     = 'CUSTOMER',     'Client / End Customer'

    role = models.CharField(
        max_length=20, 
        choices=Roles.choices, 
        default=Roles.CUSTOMER
    )
    phone_number = models.CharField(max_length=20, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} - ({self.role})"