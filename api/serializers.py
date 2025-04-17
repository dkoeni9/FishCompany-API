from django.contrib.auth import get_user_model

from .models import Company, Fish, FishBase, FishInBase, User
from rest_framework import serializers
from djoser.conf import settings
from djoser.serializers import (
    UserCreateSerializer,
    UserDeleteSerializer,
    TokenSerializer,
)


class CompanySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()

    class Meta:
        model = Company
        fields = "__all__"


class FishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fish
        fields = "__all__"


class FishBaseSerializer(serializers.ModelSerializer):
    fish_count = serializers.SerializerMethodField()

    def get_fish_count(self, obj):
        return obj.fish.count()

    class Meta:
        model = FishBase
        fields = (
            "id",
            "latitude",
            "longitude",
            "address",
            "name",
            "description",
            "price_per_hour",
            "entry_price",
            "fish_count",
        )


class SimpleFishBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FishBase
        fields = ("id", "name", "address")


class FBFishesSerializer(serializers.ModelSerializer):
    fish_id = serializers.IntegerField(write_only=True)
    id = serializers.IntegerField(source="fish.id", read_only=True)
    name = serializers.CharField(source="fish.name", read_only=True)
    description = serializers.CharField(source="fish.description", read_only=True)

    class Meta:
        model = FishInBase
        fields = ["fish_id", "id", "name", "description", "price_per_kilo"]


class CompanyCreateSerializer(UserCreateSerializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    middle_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    name = serializers.CharField()  # обязательно указывать?
    address = serializers.CharField()

    class Meta:
        model = User
        fields = (settings.USER_ID_FIELD, settings.LOGIN_FIELD, "password") + tuple(
            User.REQUIRED_FIELDS
        )
        fields += ("name", "address")


class StaffSerializer(serializers.ModelSerializer):
    works_on_fish_base_id = serializers.CharField(write_only=True)
    fish_base = SimpleFishBaseSerializer(source="works_on_fish_base", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "works_on_fish_base_id",
            "fish_base",
        )


class StaffCreateSerializer(UserCreateSerializer):
    works_on_fish_base = serializers.PrimaryKeyRelatedField(
        queryset=FishBase.objects.all(), write_only=True
    )
    description = serializers.CharField(
        source="fish_base_worker_description", write_only=True, allow_blank=True
    )

    class Meta:
        model = User
        fields = (settings.USER_ID_FIELD, settings.LOGIN_FIELD, "password") + tuple(
            User.REQUIRED_FIELDS
        )
        fields += (
            "works_on_fish_base",
            "description",
        )


class CustomUserDeleteSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = []


class CustomTokenSerializer(TokenSerializer):
    token = serializers.CharField(source="key")
    id = serializers.IntegerField(source="user.pk")
    username = serializers.CharField(source="user.username")
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        user = obj.user
        return f"{user.first_name} {user.last_name}".strip()

    def get_role(self, obj):
        user = obj.user
        if user.groups.exists():
            return user.groups.first().name
        return "DefaultRole"

    class Meta(TokenSerializer.Meta):
        fields = ("id", "username", "full_name", "role", "token")
