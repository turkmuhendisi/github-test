"""
Log Analytics URL Configuration
"""

from django.urls import path
from . import views

app_name = 'log_analytics'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # API endpoints
    path('api/overview/', views.OverviewAPIView.as_view(), name='api_overview'),
    path('api/trend/daily/', views.DailyTrendAPIView.as_view(), name='api_daily_trend'),
    path('api/trend/hourly/', views.HourlyTrendAPIView.as_view(), name='api_hourly_trend'),
    path('api/endpoints/top/', views.TopEndpointsAPIView.as_view(), name='api_top_endpoints'),
    path('api/errors/', views.ErrorsAPIView.as_view(), name='api_errors'),
    path('api/errors/<int:pk>/resolve/', views.ResolveErrorAPIView.as_view(), name='api_resolve_error'),
    path('api/status-distribution/', views.StatusDistributionAPIView.as_view(), name='api_status_distribution'),
]

