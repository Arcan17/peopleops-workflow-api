from rest_framework import serializers
from .models import Employee
from apps.accounts.serializers import UserSerializer, UserCreateSerializer


class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id", "user", "full_name", "email",
            "position", "department", "hire_date",
            "contract_type", "base_salary", "status",
            "manager", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EmployeeCreateSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer()

    class Meta:
        model = Employee
        fields = [
            "user", "position", "department", "hire_date",
            "contract_type", "base_salary", "status", "manager",
        ]

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        from apps.accounts.models import CustomUser
        user = CustomUser.objects.create_user(**user_data)
        return Employee.objects.create(user=user, **validated_data)


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["position", "department", "hire_date", "contract_type", "base_salary", "status", "manager"]
