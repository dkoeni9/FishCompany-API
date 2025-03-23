from django.contrib.auth import get_user_model

from .models import Fish, FishBase, User
from rest_framework import serializers
from djoser.serializers import TokenSerializer


class FishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fish
        fields = "__all__"


class FishBaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = FishBase
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class UserCompanySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(source="company_name")
    address = serializers.CharField(source="company_address")

    class Meta:
        model = User
        fields = ("id", "name", "address")


User = get_user_model()


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
