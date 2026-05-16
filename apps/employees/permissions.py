from rest_framework.permissions import BasePermission
from apps.accounts.models import Role


class IsAdminUser(BasePermission):
    """Only admin users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.ADMIN)


class IsManagerOrAdmin(BasePermission):
    """Manager or admin users."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.ADMIN, Role.MANAGER)
        )
