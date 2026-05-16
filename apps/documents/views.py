from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Document
from .serializers import DocumentSerializer
from apps.employees.permissions import IsManagerOrAdmin


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related("employee", "uploaded_by").all()
    serializer_class = DocumentSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_manager_or_admin:
            return super().get_queryset()
        # Employees see only their own documents
        return super().get_queryset().filter(employee__user=user)
