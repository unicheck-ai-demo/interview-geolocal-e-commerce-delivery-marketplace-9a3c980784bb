import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point

from app.models import Address, ProductCategory
from app.services import InventoryService, MerchantService, ProductService

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
