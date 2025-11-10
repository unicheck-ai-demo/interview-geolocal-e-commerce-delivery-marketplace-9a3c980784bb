from django.contrib import admin

from .models import Address, DeliveryZone, Inventory, Merchant, Order, OrderItem, Product, ProductCategory

admin.site.register(Merchant)
admin.site.register(Product)
admin.site.register(Address)
admin.site.register(Inventory)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(DeliveryZone)
admin.site.register(ProductCategory)
