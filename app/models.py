from django.contrib.auth import get_user_model
from django.contrib.gis.db import models as gis_models
from django.db import models

User = get_user_model()


class DeliveryZone(models.Model):
    name = models.CharField(max_length=120)
    area = gis_models.PolygonField(srid=4326)

    class Meta:
        indexes = [
            gis_models.Index(
                fields=['area'],
                name='zone_area_gist',
                db_tablespace='',
            )
        ]

    def __str__(self):
        return self.name


class Address(models.Model):
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=80)
    location = gis_models.PointField(srid=4326)

    class Meta:
        indexes = [gis_models.Index(fields=['location'], name='address_location_gist')]

    def __str__(self):
        return f'{self.line1}, {self.city}'


class Merchant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='merchant_profile')
    name = models.CharField(max_length=120)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, related_name='merchant')
    categories = models.ManyToManyField('ProductCategory', related_name='merchants')
    delivery_zones = models.ManyToManyField(DeliveryZone, related_name='merchants')

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'merchant', 'category')
        indexes = [
            models.Index(fields=['merchant', 'category']),
        ]

    def __str__(self):
        return self.name


class Inventory(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='inventories')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventories')
    stock = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('merchant', 'product')


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='order_addresses')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order {self.pk} by {self.user} ({self.status})'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f'{self.product} x {self.quantity}'
