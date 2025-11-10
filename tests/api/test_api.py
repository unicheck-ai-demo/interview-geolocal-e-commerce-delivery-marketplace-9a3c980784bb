import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status

from app.models import Address, Merchant, Product, ProductCategory

pytestmark = pytest.mark.django_db


def test_create_merchant_api(api_client):
    user = User.objects.create_user(username='aa', password='pw')
    api_client.force_authenticate(user)
    category = ProductCategory.objects.create(name='Bakery')
    data = {
        'name': 'Sample Merchant',
        'address': {
            'line1': 'Addr 1',
            'line2': '',
            'city': 'City',
            'state': '',
            'postal_code': '10000',
            'country': 'CC',
            'location': {'type': 'Point', 'coordinates': [5.1, 5.3]},
        },
        'categories': [category.id],
    }
    response = api_client.post(reverse('api:merchant-list'), data, format='json')
    if response.status_code != status.HTTP_201_CREATED and response.status_code != status.HTTP_200_OK:
        print('API response errors:', response.data)
    assert response.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
    assert response.data['name'] == 'Sample Merchant'


def test_list_products_api(api_client):
    user = User.objects.create_user(username='bb', password='pw')
    addr = Address.objects.create(
        line1='X', line2='', city='B', state='', postal_code='1', country='CCC', location=Point(1, 1)
    )
    cat = ProductCategory.objects.create(name='Fruit')
    merchant = Merchant.objects.create(user=user, name='Fruit Store', address=addr)
    prod = Product.objects.create(name='Apple', description='Fresh', category=cat, merchant=merchant, price=2.5)
    url = reverse('api:product-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['results'][0]['name'] == 'Apple'


def test_nearby_products_api(api_client):
    user = User.objects.create_user(username='cx', password='pw')
    cat = ProductCategory.objects.create(name='Vegetables')
    addr = Address.objects.create(
        line1='Y1', line2='', city='L', state='', postal_code='3000', country='Z', location=Point(10, 10)
    )
    merchant = Merchant.objects.create(user=user, name='VegStore', address=addr)
    prod = Product.objects.create(name='Carrot', description='Crisp', category=cat, merchant=merchant, price=1.5)
    url = reverse('api:product-nearby')
    resp = api_client.get(url, {'lat': 10, 'lng': 10, 'radius': 2})
    assert resp.status_code == 200
    assert any(p['name'] == 'Carrot' for p in resp.data)
