import asyncio

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import DatabaseError, connection
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Inventory, Merchant, Order, Product
from app.services import DeliveryService
from app.utils.cache import get_cached_product_search, set_cached_product_search

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

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        try:
            lat = float(request.query_params['lat'])
            lng = float(request.query_params['lng'])
            radius = float(request.query_params.get('radius', 5))  # km
        except Exception:
            return Response({'detail': 'lat, lng, radius are required.'}, status=400)
        pname = request.query_params.get('product_name')
        cached = get_cached_product_search(lat, lng, radius, pname)
        if cached:
            return Response(cached)
        user_point = Point(lng, lat, srid=4326)
        qs = Product.objects.filter(
            is_published=True, merchant__address__location__distance_lte=(user_point, D(km=radius))
        )
        if pname:
            qs = qs.filter(name__icontains=pname)
        qs = (
            qs.annotate(distance=Distance('merchant__address__location', user_point))
            .select_related('merchant', 'category')
            .order_by('distance')[0:30]
        )
        res = ProductSerializer(qs, many=True).data
        set_cached_product_search(lat, lng, radius, pname, res)
        return Response(res)


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.select_related('merchant', 'product').all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('user', 'merchant', 'address').prefetch_related('items__product').all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class DeliveryETAView(APIView):
    def post(self, request):
        order_ids = request.data.get('order_ids', [])
        # In real world use async from DRF or spawn task, here event-loop is run inline for demonstration
        result = asyncio.run(DeliveryService.get_eta_for_orders(order_ids))
        return Response(result)
