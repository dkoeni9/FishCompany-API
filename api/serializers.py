from django.contrib.auth import get_user_model

from .models import Fish, FishBase
from rest_framework import serializers
from djoser.conf import settings
from djoser.serializers import (
    UserCreateSerializer,
    UserDeleteSerializer,
    TokenSerializer,
)

User = get_user_model()


class FishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fish
        fields = "__all__"


class FishBaseSerializer(serializers.ModelSerializer):
    fish_count = serializers.SerializerMethodField()
    company_name = serializers.CharField(write_only=True, required=False)

    def get_fish_count(self, obj):
        return len(obj.fish_in_base) if obj.fish_in_base else 0

    class Meta:
        model = FishBase
        fields = (
            "id",
            "company_name",
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


class FBFishesSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    price_per_kilo = serializers.DecimalField(max_digits=10, decimal_places=2)

    def to_representation(self, instance):
        name = instance.get("Name")
        price_per_kilo = instance.get("PricePerKilo")

        try:
            fish = Fish.objects.get(name=name)
            id = fish.id
            description = fish.description or ""
        except Fish.DoesNotExist:
            id = None
            description = ""

        return {
            "id": id,
            "name": name,
            "description": description,
            "price_per_kilo": price_per_kilo,
        }


class CompanySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(readon_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    middle_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    name = serializers.CharField(source="company_name")
    address = serializers.CharField(source="company_address")

    class Meta:
        model = User
        fields = ("id", "name", "address")


class CompanyCreateSerializer(UserCreateSerializer):
    id = serializers.IntegerField(readon_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    middle_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    name = serializers.CharField(source="company_name")
    address = serializers.CharField(source="company_address")

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
        source="description_worker_on_fish_base", write_only=True, allow_blank=True
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
