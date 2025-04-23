from django.contrib.auth import get_user_model

from .models import Company, Fish, FishBase, FishInBase, User, StaffProfile
from rest_framework import serializers
from djoser.conf import settings
from djoser.serializers import (
    UserCreateSerializer,
    UserDeleteSerializer,
    TokenSerializer,
)


class CompanySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Company
        fields = ("id", "name", "address")


class EntrepreneurSerializer(UserCreateSerializer):
    company = CompanySerializer()

    class Meta:
        model = User
        fields = (settings.USER_ID_FIELD, settings.LOGIN_FIELD, "password") + tuple(
            User.REQUIRED_FIELDS
        )
        fields += ("company",)

    def create(self, validated_data):
        company_data = validated_data.pop("company")

        user = User.objects.create(**validated_data)
        company.objects.create(owner=user, **company_data)

        company_serializer = CompanySerializer(data=company_data)
        company_serializer.is_valid(raise_exception=True)
        company = company_serializer.save()

        user.company = company
        user.save()

        return user


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


class FishBasePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FishBase
        fields = ("photo",)


class CompanyBasesSerializer(serializers.ModelSerializer):
    fish_bases = FishBaseSerializer(source="fishbase_set", many=True, read_only=True)

    class Meta:
        model = Company
        fields = ("id", "name", "address", "fish_bases")


class FBFishesSerializer(serializers.ModelSerializer):
    fish_id = serializers.IntegerField(write_only=True)
    id = serializers.IntegerField(source="fish.id", read_only=True)
    name = serializers.CharField(source="fish.name", read_only=True)
    description = serializers.CharField(source="fish.description", read_only=True)

    class Meta:
        model = FishInBase
        fields = ("fish_id", "id", "name", "description", "price_per_kilo")


class StaffSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    middle_name = serializers.CharField(source="user.middle_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    fish_base = SimpleFishBaseSerializer(read_only=True)

    class Meta:
        model = StaffProfile
        fields = (
            "id",
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "fish_base",
        )


class StaffCreateSerializer(UserCreateSerializer):
    fish_base_id = serializers.PrimaryKeyRelatedField(
        queryset=FishBase.objects.all(), write_only=True
    )
    description = serializers.CharField(write_only=True, allow_blank=True)

    class Meta:
        model = User
        fields = (settings.USER_ID_FIELD, settings.LOGIN_FIELD, "password") + tuple(
            User.REQUIRED_FIELDS
        )
        fields += ("description", "fish_base_id")

    def validate_fish_base_id(self, fish_base):
        user = self.context["request"].user

        if fish_base.company != user.company:
            raise serializers.ValidationError(
                "Fish base does not belong to your company."
            )

        return fish_base

    def validate(self, attrs):
        attrs.pop("fish_base_id", None)
        attrs.pop("description", None)

        return super().validate(attrs)

    def create(self, validated_data):
        fish_base_id = self.initial_data.get("fish_base_id")
        description = self.initial_data.get("description", "")

        user = super().create(validated_data)

        fish_base = FishBase.objects.get(pk=fish_base_id)

        StaffProfile.objects.create(
            user=user, fish_base=fish_base, description=description
        )
        return user


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
        return None

    class Meta(TokenSerializer.Meta):
        fields = ("id", "username", "full_name", "role", "token")
