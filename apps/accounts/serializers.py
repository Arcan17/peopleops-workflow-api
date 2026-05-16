from rest_framework import serializers

from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "email", "first_name", "last_name", "full_name", "role", "is_active", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ["email", "first_name", "last_name", "role", "password"]

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)
