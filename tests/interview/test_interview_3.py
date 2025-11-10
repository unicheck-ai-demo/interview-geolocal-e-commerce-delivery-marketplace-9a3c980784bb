import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point, Polygon
from django.urls import reverse

from app.models import Address, DeliveryZone, Merchant, Product, ProductCategory

pytestmark = pytest.mark.django_db


@pytest.mark.xfail(strict=True)
def test_products_in_zone(api_client):
    zone = DeliveryZone.objects.create(
        name='TestZone', area=Polygon(((-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)), srid=4326)
    )
    address = Address.objects.create(
        line1='Addr', line2='', city='City', state='', postal_code='00000', country='C', location=Point(0, 0, srid=4326)
    )
    user = User.objects.create_user(username='zoneuser', password='pw')
    merchant = Merchant.objects.create(user=user, name='ZoneMerchant', address=address)
    merchant.delivery_zones.add(zone)
    category = ProductCategory.objects.create(name='ZoneCat')
    product = Product.objects.create(name='ZoneProd', description='', category=category, merchant=merchant, price=5.00)
    url = reverse('api:products-in-zone')
    response = api_client.get(url, {'zone_id': zone.id})
    assert response.status_code == 200
    data = response.data
    assert isinstance(data, list)
    assert any(item.get('id') == product.id for item in data)
    assert any(item.get('name') == 'ZoneProd' for item in data)
