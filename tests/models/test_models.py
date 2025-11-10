import pytest
from django.contrib.gis.geos import Point, Polygon

from app.models import Address, DeliveryZone, ProductCategory

pytestmark = pytest.mark.django_db


def test_product_category_str():
    cat = ProductCategory.objects.create(name='Groceries')
    assert str(cat) == 'Groceries'


def test_address_and_deliveryzone_geo():
    addr = Address.objects.create(
        line1='123 Example',
        line2='',
        city='Testville',
        state='TS',
        postal_code='10101',
        country='Neverland',
        location=Point(1, 1),
    )
    assert 'Testville' in str(addr)
    zone = DeliveryZone.objects.create(name='Zone1', area=Polygon(((0, 0), (0, 3), (3, 3), (3, 0), (0, 0))))
    assert zone.area.srid == 4326
