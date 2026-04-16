from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()
router.include_root_view = False
router.register(r'categories', api_views.CategoryViewSet, basename='category')
router.register(r'books', api_views.BookViewSet, basename='book')
router.register(r'sessions', api_views.ReadingSessionViewSet, basename='session')

urlpatterns = [
    path('auth/token/', obtain_auth_token, name='api_obtain_auth_token'),
    path('', api_views.api_usage_guide, name='api_usage_guide'),
    path('', include(router.urls)),
]
