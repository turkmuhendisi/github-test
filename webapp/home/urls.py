"""
Webapp Home URL'leri
====================

Ana sayfa ve temel sayfa URL'leri.
config/urls/webapp.py tarafından include edilir.

Namespace: home
Örnek: {% url 'home:index' %}
"""

from django.urls import path
from django.http import HttpResponse

from . import views

# =============================================================================
# APP NAME (namespace için zorunlu)
# =============================================================================

app_name = 'home'

# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    # Ana sayfa
    path('', views.index, name='index'),
    
    # Diğer sayfalar
    path('kripto/', views.kripto, name='kripto'),
    path('wizardList/', views.belgeNet_wizardList, name='wizardList'),
    
    # API endpoints
    path('slides/', views.slides_json, name='slides-json'),
    
    # Chrome DevTools fix
    path('.well-known/appspecific/com.chrome.devtools.json', 
         lambda r: HttpResponse('{}', content_type='application/json'),
         name='chrome-devtools'),
]