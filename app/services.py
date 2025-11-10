from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F

from app.constants import ORDER_STATUS_PENDING
from app.models import Inventory, Merchant, Order, OrderItem, Product

User = get_user_model()


class MerchantService:
    @staticmethod
    def create_merchant(user, name, address, categories=None, delivery_zones=None):
        merchant = Merchant.objects.create(user=user, name=name, address=address)
        if categories:
            merchant.categories.set(categories)
        if delivery_zones:
            merchant.delivery_zones.set(delivery_zones)
        return merchant

    @staticmethod
    def get_merchant(pk):
        return Merchant.objects.select_related('address').prefetch_related('categories', 'delivery_zones').get(pk=pk)


class ProductService:
    @staticmethod
    def create_product(merchant, name, category, price, description=''):
        return Product.objects.create(
            merchant=merchant, name=name, category=category, price=price, description=description
        )

    @staticmethod
    def publish_product(product: Product):
        product.is_published = True
        product.save(update_fields=['is_published'])
        return product

    @staticmethod
    def unpublish_product(product: Product):
        product.is_published = False
        product.save(update_fields=['is_published'])
        return product


class InventoryService:
    @staticmethod
    def set_stock(merchant, product, quantity):
        inv, _ = Inventory.objects.get_or_create(merchant=merchant, product=product, defaults={'stock': 0})
        inv.stock = quantity
        inv.save()
        return inv

    @staticmethod
    @transaction.atomic
    def decrement_stock_atomic(merchant, product, quantity):
        inv = Inventory.objects.select_for_update().get(merchant=merchant, product=product)
        if inv.stock < quantity:
            raise ValueError('Insufficient stock')
        inv.stock = F('stock') - quantity
        inv.save()
        inv.refresh_from_db()
        return inv


class OrderService:
    @staticmethod
    @transaction.atomic
    def place_order(user, merchant, address, items):
        order = Order.objects.create(
            user=user, merchant=merchant, address=address, status=ORDER_STATUS_PENDING, total=0
        )
        total = 0
        sid = transaction.savepoint()
        try:
            for prod, qty in items:
                InventoryService.decrement_stock_atomic(merchant, prod, qty)
                line_total = prod.price * qty
                total += line_total
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    quantity=qty,
                    unit_price=prod.price,
                    line_total=line_total,
                )
            order.total = total
            order.status = ORDER_STATUS_PENDING
            order.save()
        except Exception:
            transaction.savepoint_rollback(sid)
            raise
        transaction.savepoint_commit(sid)
        return order
