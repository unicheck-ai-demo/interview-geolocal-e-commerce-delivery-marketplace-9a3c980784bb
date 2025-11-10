from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DeliveryETAView,
    HealthCheckView,
    InventoryViewSet,
    MerchantViewSet,
    OrderAnalyticsView,
    OrderViewSet,
    PriorityAssignmentView,
    ProductNearbyView,
    ProductsInZoneView,
    ProductViewSet,
)

router = DefaultRouter()
router.register(r'merchants', MerchantViewSet, basename='merchant')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'inventories', InventoryViewSet, basename='inventory')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('custom/products/nearby/', ProductNearbyView.as_view(), name='product-nearby'),
    path('custom/products/in-zone/', ProductsInZoneView.as_view(), name='products-in-zone'),
    path('delivery/eta/', DeliveryETAView.as_view(), name='delivery-eta'),
    path('custom/orders/priority-assignment/', PriorityAssignmentView.as_view(), name='priority-assignment'),
    path('custom/orders/analytics/', OrderAnalyticsView.as_view(), name='order-analytics'),
]

app_name = 'api'
