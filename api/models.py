# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class Fish(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "fish"


class FishBase(models.Model):
    company_name = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )
    address = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price_per_hour = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    entry_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    fish_in_base = models.JSONField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "fish_base"


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("The UserLogin field must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractUser):
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    company_address = models.CharField(max_length=255, blank=True, null=True)
    works_on_fish_base = models.ForeignKey(
        FishBase, models.DO_NOTHING, blank=True, null=True
    )
    description_worker_on_fish_base = models.TextField(blank=True, null=True)

    email = None
    date_joined = None
    last_login = None

    # Side Note: If you are extending PermissionsMixin to your custom user than you do not need is_superuser to be defined explicitly, PermissionsMixin already have this in it.

    objects = CustomUserManager()

    # REQUIRED_FIELDS = ["first_name", "middle_name", "last_name"]
    REQUIRED_FIELDS = ["first_name", "middle_name", "last_name"]

    class Meta:
        managed = True
        db_table = "user"
