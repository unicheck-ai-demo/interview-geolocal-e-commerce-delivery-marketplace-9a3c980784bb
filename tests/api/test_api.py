import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status

from app.models import Address, Merchant, Order, OrderItem, Product, ProductCategory

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


def test_order_analytics(api_client):
    user = User.objects.create_user(username='mmm', password='pw')
    cat = ProductCategory.objects.create(name='Bulk')
    addr = Address.objects.create(
        line1='11', line2='11', city='K', state='Y', postal_code='10', country='QC', location=Point(7, 7)
    )
    merchant = Merchant.objects.create(user=user, name='TopOrderSt', address=addr)
    prod = Product.objects.create(name='Banana', description='Win', category=cat, merchant=merchant, price=1.5)
    order = Order.objects.create(user=user, merchant=merchant, address=addr, status='fulfilled', total=12)
    OrderItem.objects.create(order=order, product=prod, quantity=6, unit_price=1.5, line_total=9)
    url = reverse('api:order-analytics')
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert any('Banana' in str(r.get('product__name')) for r in resp.data)


def test_priority_assignment_api(api_client):
    user = User.objects.create_user(username='de', password='pw')
    api_client.force_authenticate(user)
    cat = ProductCategory.objects.create(name='Drv')
    addr = Address.objects.create(
        line1='N1', line2='', city='A', state='', postal_code='B3', country='PL', location=Point(12, 8)
    )
    merchant = Merchant.objects.create(user=user, name='DrSt', address=addr)
    order = Order.objects.create(user=user, merchant=merchant, address=addr, status='pending', total=10)
    url = reverse('api:priority-assignment')
    data = {
        'order_id': order.pk,
        'courier_locations': [
            {'id': 1, 'lat': 12, 'lng': 8},
            {'id': 2, 'lat': 13, 'lng': 8},
        ],
    }
    resp = api_client.post(url, data, format='json')
    assert resp.status_code == 200
    assert resp.data.get('assigned', {}).get('courier_id') == 1


def test_auth_required_for_post_endpoints(api_client):
    # Unauthenticated POST to /api/merchants/ should return 401
    category = ProductCategory.objects.create(name='AuthT1')
    data = {
        'name': 'Auth Protected Merchant',
        'address': {
            'line1': 'A',
            'line2': '',
            'city': 'X',
            'state': 'Q',
            'postal_code': '10000',
            'country': 'Y',
            'location': {'type': 'Point', 'coordinates': [1.0, 2.0]},
        },
        'categories': [category.id],
    }
    resp = api_client.post(reverse('api:merchant-list'), data, format='json')
    assert resp.status_code == 401

    # Unauthenticated POST to /api/orders/ should return 401
    resp2 = api_client.post(reverse('api:order-list'), data={}, format='json')
    assert resp2.status_code == 401
