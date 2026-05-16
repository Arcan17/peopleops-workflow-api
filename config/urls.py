from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def api_root(_request):
    return JsonResponse(
        {
            "name": "PeopleOps Workflow API",
            "version": "1.0.0",
            "docs": "/api/docs/",
            "schema": "/api/schema/",
            "resources": {
                "auth": "/api/auth/token/",
                "employees": "/api/employees/",
                "requests": "/api/requests/",
                "approvals": "/api/approvals/",
                "documents": "/api/documents/",
                "notifications": "/api/notifications/",
                "reports": "/api/reports/",
            },
        }
    )

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api_root, name="api-root"),

    # Auth
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Apps
    path("api/employees/", include("apps.employees.urls")),
    path("api/requests/", include("apps.requests.urls")),
    path("api/approvals/", include("apps.approvals.urls")),
    path("api/documents/", include("apps.documents.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/reports/", include("apps.reports.urls")),

    # OpenAPI docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
