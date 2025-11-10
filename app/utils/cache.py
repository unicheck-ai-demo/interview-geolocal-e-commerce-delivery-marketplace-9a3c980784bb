import hashlib
import json

from django.core.cache import cache

CACHE_VERSION = 'v2'


def _versioned_key(base, *args):
    key = f'{CACHE_VERSION}:{base}:' + ':'.join([str(a) for a in args])
    return hashlib.sha256(key.encode()).hexdigest()


def get_cached_product_search(lat, lng, radius_m, pname=None):
    key = _versioned_key('product_search', lat, lng, radius_m, pname or '')
    val = cache.get(key)
    if val:
        return json.loads(val)
    return None


def set_cached_product_search(lat, lng, radius_m, pname, data, timeout=120):
    key = _versioned_key('product_search', lat, lng, radius_m, pname or '')
    cache.set(key, json.dumps(data), timeout=timeout)


def invalidate_product_cache(*args, **kwargs):
    # For future: could scan/delete keys by version prefix when stock is updated
    pass
