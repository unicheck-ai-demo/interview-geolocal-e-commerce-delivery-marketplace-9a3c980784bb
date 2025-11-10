from threading import Thread

import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point

from app.models import Address, Merchant, Product, ProductCategory
from app.services import InventoryService, MerchantService, OrderService, ProductService

pytestmark = pytest.mark.django_db


def test_create_and_get_merchant():
    user = User.objects.create_user(username='owner', password='pw')
    addr = Address.objects.create(
        line1='L1', line2='', city='A', state='', postal_code='0000', country='C', location=Point(2, 2)
    )
    pc = ProductCategory.objects.create(name='Food')
    merchant = MerchantService.create_merchant(user, 'M1', addr, categories=[pc])
    m_retrieved = MerchantService.get_merchant(merchant.pk)
    assert m_retrieved.name == 'M1'
    assert m_retrieved.categories.count() == 1


def test_inventory_set_and_decrement():
    user = User.objects.create_user(username='own2', password='pw')
    addr = Address.objects.create(
        line1='L2', line2='', city='B', state='', postal_code='1111', country='C', location=Point(1, 1)
    )
    pc = ProductCategory.objects.create(name='Drinks')
    merchant = MerchantService.create_merchant(user, 'M2', addr, categories=[pc])
    product = ProductService.create_product(merchant, 'Cola', pc, 9.90)
    inv = InventoryService.set_stock(merchant, product, 10)
    assert inv.stock == 10
    inv2 = InventoryService.decrement_stock_atomic(merchant, product, 3)
    assert inv2.stock == 7


def test_concurrent_inventory_decrement(transactional_db):
    user = User.objects.create_user(username='threaded', password='pw')
    addr = Address.objects.create(
        line1='T1', line2='', city='W', state='', postal_code='XY', country='QQ', location=Point(3, 3)
    )
    cat = ProductCategory.objects.create(name='Snacks')
    merchant = MerchantService.create_merchant(user, 'ThreadStore', addr, categories=[cat])
    product = ProductService.create_product(merchant, 'Cookie', cat, 2.22)
    InventoryService.set_stock(merchant, product, 5)
    user_pk = user.pk
    merchant_pk = merchant.pk
    addr_pk = addr.pk
    product_pk = product.pk

    results = []

    def place():
        from app.models import Address, User

        u = User.objects.get(pk=user_pk)
        m = Merchant.objects.get(pk=merchant_pk)
        a = Address.objects.get(pk=addr_pk)
        p = Product.objects.get(pk=product_pk)
        try:
            OrderService.place_order(u, m, a, [(p, 3)])
            results.append('success')
        except Exception as e:
            results.append(str(e))

    t1 = Thread(target=place)
    t2 = Thread(target=place)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert results.count('success') == 1
    assert any('stock' in r or 'Insufficient' in r for r in results)
