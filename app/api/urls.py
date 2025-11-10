from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DeliveryETAView, HealthCheckView, InventoryViewSet, MerchantViewSet, OrderViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'merchants', MerchantViewSet, basename='merchant')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'inventories', InventoryViewSet, basename='inventory')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('delivery/eta/', DeliveryETAView.as_view(), name='delivery-eta'),
]

app_name = 'api'
