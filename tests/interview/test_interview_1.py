import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.urls import reverse

from app.models import Address, Merchant, Product, ProductCategory

pytestmark = pytest.mark.django_db


@pytest.mark.xfail(strict=True)
def test_product_price_numeric_in_api(api_client):
    user = User.objects.create_user(username='testpr', password='pw')
    address = Address.objects.create(
        line1='Addr', line2='', city='City', state='', postal_code='00000', country='C', location=Point(0, 0)
    )
    category = ProductCategory.objects.create(name='TestCat')
    merchant = Merchant.objects.create(user=user, name='TestMerchant', address=address)
    Product.objects.create(name='TestProduct', description='', category=category, merchant=merchant, price=12.34)
    url = reverse('api:product-list')
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.data['results'][0]
    assert isinstance(data['price'], (int, float))
