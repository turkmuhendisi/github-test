"""
Log Analytics Views
===================

Analytics dashboard ve API.
"""

import json
from datetime import date, timedelta

from django.http import JsonResponse, HttpRequest
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

from .services import AnalyticsService
from .models import ErrorLog


@method_decorator(staff_member_required, name='dispatch')
class DashboardView(TemplateView):
    """Analytics dashboard."""
    template_name = 'logs/analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Overview
        context['overview'] = AnalyticsService.get_overview(days=7)
        
        # Trends
        context['daily_trend'] = json.dumps(AnalyticsService.get_daily_trend(days=30))
        context['hourly_trend'] = json.dumps(AnalyticsService.get_hourly_trend(hours=24))
        
        # Endpoints
        context['top_endpoints'] = AnalyticsService.get_top_endpoints(days=7, limit=10)
        context['slowest_endpoints'] = AnalyticsService.get_slowest_endpoints(days=7, limit=5)
        context['error_endpoints'] = AnalyticsService.get_error_endpoints(days=7, limit=5)
        
        # Errors
        context['recent_errors'] = AnalyticsService.get_recent_errors(limit=10)
        
        # Status distribution
        context['status_distribution'] = json.dumps(AnalyticsService.get_status_distribution(days=7))
        
        context['page_title'] = 'Log Analytics'
        
        return context


# =============================================================================
# API VIEWS
# =============================================================================

@method_decorator(staff_member_required, name='dispatch')
class OverviewAPIView(View):
    """Overview API."""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        days = int(request.GET.get('days', 7))
        data = AnalyticsService.get_overview(days=days)
        return JsonResponse({'success': True, 'data': data})


@method_decorator(staff_member_required, name='dispatch')
class DailyTrendAPIView(View):
    """Daily trend API."""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        days = int(request.GET.get('days', 30))
        data = AnalyticsService.get_daily_trend(days=days)
        return JsonResponse({'success': True, 'data': data})


@method_decorator(staff_member_required, name='dispatch')
class HourlyTrendAPIView(View):
    """Hourly trend API."""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        hours = int(request.GET.get('hours', 24))
        data = AnalyticsService.get_hourly_trend(hours=hours)
        return JsonResponse({'success': True, 'data': data})


@method_decorator(staff_member_required, name='dispatch')
class TopEndpointsAPIView(View):
    """Top endpoints API."""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        days = int(request.GET.get('days', 7))
        limit = int(request.GET.get('limit', 10))
        data = AnalyticsService.get_top_endpoints(days=days, limit=limit)
        return JsonResponse({'success': True, 'data': data})


@method_decorator(staff_member_required, name='dispatch')
class ErrorsAPIView(View):
    """Errors API."""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        limit = int(request.GET.get('limit', 20))
        data = AnalyticsService.get_recent_errors(limit=limit)
        return JsonResponse({'success': True, 'data': data})


@method_decorator(staff_member_required, name='dispatch')
class ResolveErrorAPIView(View):
    """Error resolve API."""
    
    def post(self, request: HttpRequest, pk: int) -> JsonResponse:
        try:
            error = ErrorLog.objects.get(pk=pk)
            error.resolve(user=request.user.username)
            return JsonResponse({'success': True, 'message': 'Hata çözüldü olarak işaretlendi'})
        except ErrorLog.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Hata bulunamadı'}, status=404)


@method_decorator(staff_member_required, name='dispatch')
class StatusDistributionAPIView(View):
    """Status distribution API."""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        days = int(request.GET.get('days', 7))
        data = AnalyticsService.get_status_distribution(days=days)
        return JsonResponse({'success': True, 'data': data})

