# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import Value
from django.db.models.functions import Now
from django.utils import timezone


class User(AbstractUser):
    middle_name = models.CharField(max_length=50, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False, db_default=Value(False))
    is_staff = models.BooleanField(default=False, db_default=Value(False))
    is_active = models.BooleanField(default=True, db_default=Value(True))
    date_joined = models.DateTimeField(default=timezone.now, db_default=Now())
    last_login = models.DateTimeField(blank=True, null=True)

    REQUIRED_FIELDS = ["first_name", "middle_name", "last_name"]

    def __str__(self):
        return self.username

    class Meta:
        managed = True
        db_table = "user"


class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="company",
    )

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = "company"
        verbose_name_plural = "companies"


class Fish(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = "fish"
        verbose_name_plural = "fishes"


def fishbase_photo_path(instance, filename):
    return f"Photos/FishBases/{instance.id}.jpg"


class FishBase(models.Model):
    company = models.ForeignKey(Company, models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    fish = models.ManyToManyField(Fish, through="FishInBase", related_name="bases")
    photo = models.ImageField(upload_to=fishbase_photo_path, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"'{self.name}' base of '{self.company.name}' company"

    class Meta:
        managed = True
        db_table = "fish_base"


class StaffProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="staff_profile"
    )
    fish_base = models.ForeignKey(
        FishBase, on_delete=models.CASCADE, related_name="staff", blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.fish_base.name}"

    class Meta:
        managed = True
        db_table = "staff_profile"


class FishInBase(models.Model):
    fish_base = models.ForeignKey(FishBase, on_delete=models.CASCADE)
    fish = models.ForeignKey(Fish, on_delete=models.CASCADE)
    price_per_kilo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("fish_base", "fish")
