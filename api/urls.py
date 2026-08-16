from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('inventory', views.InventoryViewSet, basename='inventory')
router.register('wanted', views.WantedViewSet, basename='wanted')
router.register('offers', views.OfferViewSet, basename='offers')

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('places/', views.places, name='places'),
    path('sets/', views.sets, name='sets'),
    path('sets/<str:set_id>/cards/', views.set_cards, name='set_cards'),
    path('cards/search/', views.card_search, name='card_search'),
    path('matches/', views.matches, name='matches'),
    path('matches/<int:user_id>/', views.match_detail, name='match_detail'),
    path('matches/<int:user_id>/rest/', views.match_rest_inventory, name='match_rest_inventory'),
    path('', include(router.urls)),
]