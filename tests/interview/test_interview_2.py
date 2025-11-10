import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.urls import reverse

from app.models import Address, Merchant, Product, ProductCategory
from app.services import ProductService

pytestmark = pytest.mark.django_db


@pytest.mark.xfail(strict=True)
def test_product_nearby_cache_invalidation(api_client):
    user = User.objects.create_user(username='cachetest', password='pw')
    cat = ProductCategory.objects.create(name='CacheCat')
    addr = Address.objects.create(
        line1='Addr1', line2='', city='City', state='', postal_code='00000', country='C', location=Point(0, 0)
    )
    merchant = Merchant.objects.create(user=user, name='CacheMerchant', address=addr)
    prod = Product.objects.create(name='CacheProd', description='', category=cat, merchant=merchant, price=9.99)
    url = reverse('api:product-nearby')
    params = {'lat': 0, 'lng': 0, 'radius': 1}
    resp1 = api_client.get(url, params)
    assert resp1.status_code == 200
    names1 = [p['name'] for p in resp1.data]
    assert 'CacheProd' in names1
    ProductService.unpublish_product(prod)
    resp2 = api_client.get(url, params)
    assert resp2.status_code == 200
    names2 = [p['name'] for p in resp2.data]
    assert 'CacheProd' not in names2
