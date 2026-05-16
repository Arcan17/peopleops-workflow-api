from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Approval
from .serializers import ApprovalSerializer
from apps.employees.permissions import IsManagerOrAdmin


class ApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Approval.objects.select_related("approver", "request").all()
    serializer_class = ApprovalSerializer
    permission_classes = [IsManagerOrAdmin]
    ordering = ["-decided_at"]
