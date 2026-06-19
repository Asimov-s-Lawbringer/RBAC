"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rbac_auth.views import LoginView, MeView, RecordListView, AuditLogListView, MatrixView, AdminUserListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', LoginView.as_view(), name='api_login'),
    path('api/auth/me/', MeView.as_view(), name='api_me'),
    path('api/records/', RecordListView.as_view(), name='api_records'),
    path('api/admin/audit-logs/', AuditLogListView.as_view(), name='api_audit_logs'),
    path('api/admin/matrix/', MatrixView.as_view(), name='api_matrix'),
    path('api/admin/users/', AdminUserListView.as_view(), name='api_admin_users'),
    path('api/admin/users/<int:pk>/', AdminUserListView.as_view(), name='api_admin_user_detail')
]
