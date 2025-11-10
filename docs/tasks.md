# Interview Tasks

## Task 1: Product API price type

There is an issue with the Product API: the price is being returned as a string in the JSON response, but it should be a numeric type. Please fix the API so that `price` is returned as a number in the JSON response.

## Task 2: Refactor caching to prevent stale product search results

The product search API caches results to speed up repeated queries. However, when a product’s status is changed (for example, it is unpublished), the old results can remain in the cache indefinitely. Please refactor the caching mechanism so that search results are properly invalidated when a product’s published status changes.

## Task 3: Products by Delivery Zone

Customers need to see which products they can order based on delivery areas. The system offers a way to list products for a selected delivery region, but currently the product list always comes back empty even when merchants deliver to that region. Please implement the functionality so that when a delivery zone is specified, the API returns all available products sold by merchants that serve that zone.
