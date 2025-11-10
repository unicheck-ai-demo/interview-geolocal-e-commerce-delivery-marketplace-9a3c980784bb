import asyncio

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import DatabaseError, connection
from django.db.models import F, Sum, Window
from django.db.models.functions import Rank
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Address, DeliveryZone, Inventory, Merchant, Order, OrderItem, Product
from app.services import DeliveryService, InventoryService, MerchantService, OrderService, ProductService
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
        validated = serializer.validated_data.copy()
        user = self.request.user
        address_data = validated.pop('address')
        address = Address.objects.create(**address_data)
        categories = validated.pop('categories', [])
        merchant = MerchantService.create_merchant(user, validated['name'], address=address, categories=categories)
        serializer.instance = merchant

    def perform_update(self, serializer):
        serializer.save()


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related('merchant', 'category')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        validated = serializer.validated_data
        merchant = validated['merchant']
        category = validated['category']
        product = ProductService.create_product(
            merchant=merchant,
            name=validated['name'],
            category=category,
            price=validated['price'],
            description=validated.get('description', ''),
        )
        serializer.instance = product

    def perform_update(self, serializer):
        serializer.save()


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.select_related('merchant', 'product').all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        validated = serializer.validated_data
        merchant = validated['merchant']
        product = validated['product']
        stock = validated['stock']
        inv = InventoryService.set_stock(merchant, product, stock)
        serializer.instance = inv

    def perform_update(self, serializer):
        validated = serializer.validated_data
        merchant = validated['merchant']
        product = validated['product']
        stock = validated['stock']
        inv = InventoryService.set_stock(merchant, product, stock)
        serializer.instance = inv


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('user', 'merchant', 'address').prefetch_related('items__product').all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        validated = serializer.validated_data
        user = validated['user']
        merchant = validated['merchant']
        address = validated['address']
        items_data = self.request.data.get('items', [])
        items = []
        for item in items_data:
            prod_id = item.get('product')
            qty = item.get('quantity')
            prod = Product.objects.get(pk=prod_id)
            items.append((prod, int(qty)))
        order = OrderService.place_order(user, merchant, address, items)
        serializer.instance = order

    def perform_update(self, serializer):
        serializer.save()


class ProductNearbyView(APIView):
    http_method_names = ['get']

    def get(self, request):
        try:
            lat = float(request.query_params['lat'])
            lng = float(request.query_params['lng'])
            radius = float(request.query_params.get('radius', 5))
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


class OrderAnalyticsView(APIView):
    http_method_names = ['get']

    def get(self, request):
        qs = (
            OrderItem.objects.values('product__id', 'product__name', 'order__merchant__id', 'order__merchant__name')
            .annotate(total_sales=Sum('line_total'))
            .annotate(
                rank=Window(
                    expression=Rank(), partition_by=[F('order__merchant__id')], order_by=F('total_sales').desc()
                )
            )
            .filter(rank=1)
        )
        return Response(list(qs))


class DeliveryETAView(APIView):
    def post(self, request):
        order_ids = request.data.get('order_ids', [])
        result = asyncio.run(DeliveryService.get_eta_for_orders(order_ids))
        return Response(result)


class PriorityAssignmentView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def post(self, request):
        order_id = request.data.get('order_id')
        courier_locations = request.data.get('courier_locations', [])
        try:
            order = Order.objects.select_related('merchant__address').get(pk=order_id)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found'}, status=404)
        m_loc = order.merchant.address.location
        scored = []
        for c in courier_locations:
            c_point = Point(c['lng'], c['lat'], srid=4326)
            dist = m_loc.distance(c_point)
            scored.append({'courier_id': c['id'], 'score': dist})
        assigned = sorted(scored, key=lambda x: x['score'])[0] if scored else None
        return Response({'assigned': assigned})


class ProductsInZoneView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['get']

    def get(self, request):
        zone_id = request.query_params.get('zone_id')
        if not zone_id:
            return Response({'detail': 'zone_id is required.'}, status=400)
        try:
            _zone = DeliveryZone.objects.get(pk=zone_id)
        except DeliveryZone.DoesNotExist:
            return Response({'detail': 'Delivery zone not found.'}, status=404)
        return Response([], status=200)
