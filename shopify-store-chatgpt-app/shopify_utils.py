from __future__ import annotations
import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import aiohttp
import backoff


class ShopifyError(Exception):
    pass


class ProductNotFound(ShopifyError):
    pass


class MultipleProductsMatched(ShopifyError):
    def __init__(self, query: str, matches: List[Dict[str, Any]]):
        super().__init__(f"Multiple products matched '{query}': {[m.get('title') for m in matches][:5]}...")
        self.matches = matches


class ShopifyUtils:
    """Comprehensive Shopify store data interaction utilities."""
    
    def __init__(self, timeout_seconds: int = 25):
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.session = None
        
    def _get_api_url(self) -> str:
        """Get Shopify API URL from environment variables."""
        shop_name = os.getenv("SHOPIFY_SHOP_NAME")
        api_version = os.getenv("SHOPIFY_API_VERSION", "2024-07")
        
        if not shop_name:
            raise ShopifyError("Missing SHOPIFY_SHOP_NAME environment variable")
        
        return f"https://{shop_name}/admin/api/{api_version}/graphql.json"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        api_token = os.getenv("SHOPIFY_ADMIN_API_TOKEN")
        
        if not api_token:
            raise ShopifyError("Missing SHOPIFY_ADMIN_API_TOKEN environment variable")
        
        return {
            "X-Shopify-Access-Token": api_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @staticmethod
    def _norm(s: Optional[str]) -> str:
        """Normalize string for comparison."""
        return (s or "").strip().lower()
    
    @staticmethod
    def _display_name(s: Optional[str]) -> str:
        """Get display name from string."""
        return (s or "").strip()
    
    @staticmethod
    def _name_matches(name: str, query: str) -> bool:
        """Check if name matches query (case-insensitive)."""
        return query.lower() in name.lower()
    
    @staticmethod
    def _get_image_url(product: Dict[str, Any]) -> str:
        """Extract image URL from product data."""
        if "image" in product and product["image"]:
            return product["image"].get("src", "")
        elif "images" in product and product["images"] and len(product["images"]) > 0:
            return product["images"][0].get("src", "")
        return ""
    
    @staticmethod
    def _timestamp() -> str:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @backoff.on_exception(backoff.expo, (aiohttp.ClientError, asyncio.TimeoutError), max_time=30)
    async def _api_call(self, call, *args, **kwargs):
        """Make API call with retry logic."""
        return await call(*args, **kwargs)
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """Test API connection with a simple query."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
            
            url = self._get_api_url()
            headers = self._get_headers()
            
            # Simple GraphQL query to test connection
            query = """
            query {
                shop {
                    name
                    myshopifyDomain
                }
            }
            """
            
            payload = {"query": query}
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP Error {response.status}: {error_text}"}
                
                result = await response.json()
                
                if "errors" in result:
                    return {"success": False, "error": f"GraphQL errors: {result['errors']}"}
                
                return {"success": True, "data": result.get("data", {})}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_products(
        self,
        *,
        limit: int = 50,
        collection_id: Optional[str] = None,
        query: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None
    ) -> List[Dict[str, Any]]:
        """Get products from Shopify store."""
        owns_session = session is None
        if owns_session:
            session = aiohttp.ClientSession(timeout=self.timeout)
        
        try:
            url = self._get_api_url()
            headers = self._get_headers()
            
            # Build GraphQL query
            graphql_query = """
            query getProducts($first: Int!, $after: String, $query: String) {
                products(first: $first, after: $after, query: $query) {
                    edges {
                        node {
                            id
                            title
                            handle
                            description
                            vendor
                            tags
                            status
                            priceRangeV2 {
                                minVariantPrice {
                                    amount
                                    currencyCode
                                }
                            }
                            images(first: 1) {
                                edges {
                                    node {
                                        url
                                        altText
                                    }
                                }
                            }
                            variants(first: 5) {
                                edges {
                                    node {
                                        id
                                        title
                                        price
                                        inventoryQuantity
                                        availableForSale
                                    }
                                }
                            }
                            collections(first: 3) {
                                edges {
                                    node {
                                        title
                                        handle
                                    }
                                }
                            }
                        }
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
            """
            
            variables = {"first": limit}
            if query:
                variables["query"] = query
            payload = {"query": graphql_query, "variables": variables}
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ShopifyError(f"HTTP {response.status}: {error_text}")
                
                result = await response.json()
                
                if "errors" in result:
                    raise ShopifyError(f"GraphQL errors: {result['errors']}")
                
                products = []
                for edge in result.get("data", {}).get("products", {}).get("edges", []):
                    product = edge["node"]
                    
                    # Transform product data for UI
                    transformed_product = {
                        "id": product["id"],
                        "title": product["title"],
                        "handle": product.get("handle", ""),
                        "description": product.get("description", ""),
                        "vendor": product.get("vendor", ""),
                        "tags": product.get("tags", []),
                        "status": product.get("status", ""),
                        "price": product.get("priceRangeV2", {}).get("minVariantPrice", {}).get("amount", "0"),
                        "currency": product.get("priceRangeV2", {}).get("minVariantPrice", {}).get("currencyCode", "USD"),
                        "image_url": "",
                        "variants": [],
                        "collections": [],
                        "inventory": 0,
                        "available": False
                    }
                    
                    # Extract image URL
                    if product.get("images", {}).get("edges"):
                        transformed_product["image_url"] = product["images"]["edges"][0]["node"]["url"]
                    
                    # Extract variants and calculate inventory
                    total_inventory = 0
                    any_available = False
                    for variant_edge in product.get("variants", {}).get("edges", []):
                        variant = variant_edge["node"]
                        inventory = variant.get("inventoryQuantity", 0)
                        available = variant.get("availableForSale", False)

                        total_inventory += inventory
                        any_available = any_available or available

                        transformed_product["variants"].append({
                            "id": variant["id"],
                            "title": variant["title"],
                            "price": variant["price"],
                            "inventory": inventory,
                            "available": available
                        })

                    transformed_product["inventory"] = total_inventory
                    transformed_product["available"] = any_available

                    # Extract collections
                    for collection_edge in product.get("collections", {}).get("edges", []):
                        collection = collection_edge["node"]
                        transformed_product["collections"].append(collection["title"])
                    
                    products.append(transformed_product)
                
                return products
                
        except Exception as e:
            raise ShopifyError(f"Failed to fetch products: {str(e)}")
        finally:
            if owns_session and session:
                await session.close()
    
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """Get detailed product information including metafields."""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        
        try:
            url = self._get_api_url()
            headers = self._get_headers()
            
            # Build detailed GraphQL query
            graphql_query = """
            query getProduct($id: ID!) {
                product(id: $id) {
                    id
                    title
                    handle
                    description
                    vendor
                    tags
                    status
                    priceRangeV2 {
                        minVariantPrice {
                            amount
                            currencyCode
                        }
                    }
                    images(first: 10) {
                        edges {
                            node {
                                url
                                altText
                            }
                        }
                    }
                    variants(first: 20) {
                        edges {
                            node {
                                id
                                title
                                price
                                inventoryQuantity
                                availableForSale
                                selectedOptions {
                                    name
                                    value
                                }
                            }
                        }
                    }
                    collections(first: 5) {
                        edges {
                            node {
                                title
                                handle
                            }
                        }
                    }
                    metafields(first: 10) {
                        edges {
                            node {
                                namespace
                                key
                                value
                                type
                            }
                        }
                    }
                }
            }
            """
            
            variables = {"id": product_id}
            payload = {"query": graphql_query, "variables": variables}
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ShopifyError(f"HTTP {response.status}: {error_text}")
                
                result = await response.json()
                
                if "errors" in result:
                    raise ShopifyError(f"GraphQL errors: {result['errors']}")
                
                product_data = result.get("data", {}).get("product")
                if not product_data:
                    raise ProductNotFound(f"Product with ID {product_id} not found")
                
                # Transform product data
                transformed_product = {
                    "id": product_data["id"],
                    "title": product_data["title"],
                    "handle": product_data.get("handle", ""),
                    "description": product_data.get("description", ""),
                    "vendor": product_data.get("vendor", ""),
                    "tags": product_data.get("tags", []),
                    "status": product_data.get("status", ""),
                    "price": product_data.get("priceRangeV2", {}).get("minVariantPrice", {}).get("amount", "0"),
                    "currency": product_data.get("priceRangeV2", {}).get("minVariantPrice", {}).get("currencyCode", "USD"),
                    "images": [],
                    "variants": [],
                    "collections": [],
                    "ingredients": "",
                    "inventory": 0,
                    "available": False
                }

                # Extract images
                for image_edge in product_data.get("images", {}).get("edges", []):
                    image = image_edge["node"]
                    transformed_product["images"].append(image["url"])

                # Extract variants and calculate inventory
                total_inventory = 0
                any_available = False
                for variant_edge in product_data.get("variants", {}).get("edges", []):
                    variant = variant_edge["node"]
                    inventory = variant.get("inventoryQuantity", 0)
                    available = variant.get("availableForSale", False)

                    total_inventory += inventory
                    any_available = any_available or available

                    transformed_product["variants"].append({
                        "id": variant["id"],
                        "title": variant["title"],
                        "price": variant["price"],
                        "inventory": inventory,
                        "available": available,
                        "available": available,
                        "options": variant.get("selectedOptions", [])
                    })

                transformed_product["inventory"] = total_inventory
                transformed_product["available"] = any_available
                
                # Extract collections
                for collection_edge in product_data.get("collections", {}).get("edges", []):
                    collection = collection_edge["node"]
                    transformed_product["collections"].append(collection["title"])
                
                # Extract ingredients from metafields
                for metafield_edge in product_data.get("metafields", {}).get("edges", []):
                    metafield = metafield_edge["node"]
                    if (metafield.get("namespace") == "product" and 
                        metafield.get("key") == "ingredients"):
                        transformed_product["ingredients"] = metafield.get("value", "")
                        break
                
                return transformed_product
                
        except Exception as e:
            raise ShopifyError(f"Failed to fetch product details: {str(e)}")
    
    async def search_products(
        self,
        query: str,
        limit: int = 20,
        session: Optional[aiohttp.ClientSession] = None
    ) -> List[Dict[str, Any]]:
        """Search products using Shopify's native GraphQL search."""
        # Use server-side search for scalability
        return await self.get_products(
            query=query,
            limit=limit,
            session=session
        )
    
    async def get_product_by_title(self, title: str) -> Dict[str, Any]:
        """Get product by exact title match."""
        products = await self.search_products(title, limit=10)
        
        title_norm = self._norm(title)
        exact_matches = [
            p for p in products 
            if self._norm(p.get("title", "")) == title_norm
        ]
        
        if not exact_matches:
            raise ProductNotFound(f"No product found with title '{title}'")
        
        if len(exact_matches) > 1:
            raise MultipleProductsMatched(title, exact_matches)
        
        return exact_matches[0]

    async def get_product_by_id(
        self,
        product_id: str,
        session: Optional[aiohttp.ClientSession] = None
    ) -> Dict[str, Any]:
        """Get product by ID. Alias for get_product_details with session support."""
        owns_session = session is None
        if owns_session:
            # Use get_product_details which manages its own session
            return await self.get_product_details(product_id)
        else:
            # Temporarily store provided session and use get_product_details
            old_session = self.session
            self.session = session
            try:
                result = await self.get_product_details(product_id)
                return result
            finally:
                self.session = old_session

    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    def generate_checkout_url(self, items: List[Dict[str, Any]]) -> str:
        """
        Generate a Shopify Permalink for checkout.
        
        Args:
            items: List of dicts with 'variant_id' and 'quantity'
            
        Returns:
            str: Checkout URL
        """
        shop_name = os.getenv("SHOPIFY_SHOP_NAME")
        if not shop_name:
            return ""
            
        # Format: https://{shop}/cart/{variant_id}:{quantity},{variant_id}:{quantity}
        cart_items = []
        for item in items:
            variant_id = str(item.get("variant_id", "")).split("/")[-1]  # Extract ID from GID if needed
            quantity = item.get("quantity", 1)
            if variant_id:
                cart_items.append(f"{variant_id}:{quantity}")
                
        if not cart_items:
            return f"https://{shop_name}/cart"
            
        return f"https://{shop_name}/cart/{','.join(cart_items)}"

    async def get_cart_items_details(
        self,
        variant_ids: List[str],
        session: Optional[aiohttp.ClientSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Get details for a list of variant IDs using the nodes query.
        """
        if not variant_ids:
            return []

        owns_session = session is None
        if owns_session:
            session = aiohttp.ClientSession(timeout=self.timeout)
        
        try:
            url = self._get_api_url()
            headers = self._get_headers()
            
            # Ensure IDs are GIDs
            formatted_ids = []
            for vid in variant_ids:
                vid_str = str(vid)
                if not vid_str.startswith("gid://"):
                    formatted_ids.append(f"gid://shopify/ProductVariant/{vid_str}")
                else:
                    formatted_ids.append(vid_str)
            
            # GraphQL query to fetch multiple nodes by ID
            graphql_query = """
            query getVariants($ids: [ID!]!) {
                nodes(ids: $ids) {
                    ... on ProductVariant {
                        id
                        title
                        price
                        product {
                            title
                            images(first: 1) {
                                edges {
                                    node {
                                        url
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
            
            payload = {"query": graphql_query, "variables": {"ids": formatted_ids}}
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    return []
                
                result = await response.json()
                nodes = result.get("data", {}).get("nodes", [])
                
                details = []
                for node in nodes:
                    if not node:
                        continue
                        
                    product = node.get("product", {})
                    product_title = product.get("title", "")
                    variant_title = node.get("title", "")
                    
                    # Format title: "Product Name" or "Product Name - Variant Name"
                    full_title = product_title
                    if variant_title and variant_title != "Default Title":
                        full_title = f"{product_title} - {variant_title}"
                        
                    image_url = ""
                    if product.get("images", {}).get("edges"):
                        image_url = product["images"]["edges"][0]["node"]["url"]
                        
                    details.append({
                        "variant_id": node.get("id"),
                        "title": full_title,
                        "price": node.get("price"),
                        "image_url": image_url
                    })
                    
                return details
                
        except Exception as e:
            print(f"Error fetching cart details: {e}")
            return []
        finally:
            if owns_session and session:
                await session.close()