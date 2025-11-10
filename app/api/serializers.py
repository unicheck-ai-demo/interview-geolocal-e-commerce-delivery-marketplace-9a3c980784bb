from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from rest_framework import serializers

from app.models import Address, Inventory, Merchant, Order, OrderItem, Product, ProductCategory

User = get_user_model()


class PointField(serializers.Field):
    def to_representation(self, value):
        if not value:
            return None
        return {'type': 'Point', 'coordinates': [value.x, value.y]}

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError('Invalid type')
        if data.get('type') != 'Point':
            raise serializers.ValidationError('Geo type must be Point')
        coords = data.get('coordinates')
        if not coords or len(coords) != 2:
            raise serializers.ValidationError('coordinates must be length 2')
        return Point(coords[0], coords[1])


class AddressSerializer(serializers.ModelSerializer):
    location = PointField()

    class Meta:
        model = Address
        fields = ['id', 'line1', 'line2', 'city', 'state', 'postal_code', 'country', 'location']


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name']


class MerchantSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    address = AddressSerializer()
    categories = serializers.PrimaryKeyRelatedField(queryset=ProductCategory.objects.all(), many=True)

    class Meta:
        model = Merchant
        fields = ['id', 'user', 'name', 'address', 'categories']

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        category_ids = validated_data.pop('categories')
        user = validated_data.pop('user', None)
        address = Address.objects.create(**address_data)
        merchant = Merchant.objects.create(user=user, address=address, **validated_data)
        merchant.categories.set(category_ids)
        return merchant


class ProductSerializer(serializers.ModelSerializer):
    merchant = serializers.PrimaryKeyRelatedField(queryset=Merchant.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=ProductCategory.objects.all())

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'category', 'merchant', 'price', 'is_published', 'created_at']


class InventorySerializer(serializers.ModelSerializer):
    merchant = serializers.PrimaryKeyRelatedField(queryset=Merchant.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Inventory
        fields = ['id', 'merchant', 'product', 'stock', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'unit_price', 'line_total']


class OrderSerializer(serializers.ModelSerializer):
    merchant = serializers.PrimaryKeyRelatedField(queryset=Merchant.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())
    items = OrderItemSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = ['id', 'user', 'merchant', 'address', 'status', 'total', 'created_at', 'updated_at', 'items']
