from .models import Fish, FishBase, User
from rest_framework import serializers


class FishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fish


class FishBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FishBase


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
