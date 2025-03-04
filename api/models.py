# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import AbstractUser


class Fish(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "fish"

    def serialize(self):
        return {
            "id": self.pk,
            "name": self.name,
            "description": self.description,
        }


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
        managed = False
        db_table = "fish_base"

    def serialize(self):
        return {
            "company_name": self.company_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "name": self.name,
            "description": self.description,
            "price_per_hour": self.price_per_hour,
            "entry_price": self.entry_price,
            "fish_in_base": self.fish_in_base,
        }


class User(AbstractUser):
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    company_address = models.CharField(max_length=255, blank=True, null=True)
    # is_staff?
    works_on_fish_base = models.ForeignKey(
        FishBase, models.DO_NOTHING, blank=True, null=True
    )
    description_worker_on_fish_base = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "user"

    def serialize(self):
        return {
            "username": self.username,
            "password": self.password,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "company_name": self.company_name,
            "company_address": self.company_address,
            "works_on_fish_base": self.works_on_fish_base,
            "description_worker_on_fish_base": self.description_worker_on_fish_base,
        }
