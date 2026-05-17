from rest_framework import serializers

from apps.accounts.serializers import UserCreateSerializer, UserSerializer

from .models import Employee


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


class ManagerEmployeeUpdateSerializer(serializers.ModelSerializer):
    """
    Fields a manager is allowed to update for their direct reports.
    Sensitive fields (salary, status, manager) are intentionally excluded
    — those require admin privileges.
    """

    class Meta:
        model = Employee
        fields = ["position", "department", "hire_date", "contract_type"]


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """
    Full update serializer — admin only.
    Includes sensitive fields: base_salary, status and manager reassignment.
    """

    class Meta:
        model = Employee
        fields = ["position", "department", "hire_date", "contract_type", "base_salary", "status", "manager"]
