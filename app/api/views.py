from django.db import DatabaseError, connection
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Inventory, Merchant, Order, Product

from .serializers import InventorySerializer, MerchantSerializer, OrderSerializer, ProductSerializer


class HealthCheckView(APIView):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT PostGIS_Full_Version();')
                cursor.fetchone()
        except DatabaseError as e:
            return Response({'status': 'error', 'db': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)


class MerchantViewSet(viewsets.ModelViewSet):
    queryset = Merchant.objects.select_related('address').prefetch_related('categories', 'delivery_zones').all()
    serializer_class = MerchantSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related('merchant', 'category')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.select_related('merchant', 'product').all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('user', 'merchant', 'address').prefetch_related('items__product').all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
