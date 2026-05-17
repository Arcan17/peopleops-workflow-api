from rest_framework import viewsets

from apps.employees.permissions import IsManagerOrAdmin

from .models import Approval
from .serializers import ApprovalSerializer


class ApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Approval.objects.select_related("approver", "request").all()
    serializer_class = ApprovalSerializer
    permission_classes = [IsManagerOrAdmin]
    ordering = ["-decided_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return super().get_queryset()
        return super().get_queryset().filter(request__employee__employee_profile__manager=user)
