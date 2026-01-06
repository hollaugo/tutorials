#!/usr/bin/env python3
import os
import asyncio
from shopify_utils import ShopifyUtils

async def test_shopify():
    # Set environment variables
    os.environ['SHOPIFY_SHOP_NAME'] = '72c907-3f.myshopify.com'
    os.environ['SHOPIFY_ADMIN_API_TOKEN'] = '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'
    os.environ['SHOPIFY_API_VERSION'] = '2024-07'
    
    utils = ShopifyUtils()
    
    try:
        # Test fetching products
        print("🔍 Fetching products...")
        products = await utils.get_products(limit=5)
        print(f"Found {len(products)} products")
        
        for i, product in enumerate(products[:3], 1):
            title = product.get("title", "Unknown")
            price = product.get("price", "0")
            currency = product.get("currency", "USD")
            vendor = product.get("vendor", "Unknown")
            tags = product.get("tags", [])
            
            print(f"\n{i}. {title}")
            print(f"   Price: ${price} {currency}")
            print(f"   Vendor: {vendor}")
            print(f"   Tags: {tags}")
        
        # Test searching for essential oils
        print("\n🌿 Searching for essential oils...")
        search_results = await utils.search_products("essential oils", limit=3)
        print(f"Found {len(search_results)} essential oil products")
        
        for product in search_results:
            title = product.get("title", "Unknown")
            price = product.get("price", "0")
            print(f"- {title} (${price})")
        
        # Test searching for supplements
        print("\n💊 Searching for supplements...")
        supplement_results = await utils.search_products("supplements", limit=3)
        print(f"Found {len(supplement_results)} supplement products")
        
        for product in supplement_results:
            title = product.get("title", "Unknown")
            price = product.get("price", "0")
            print(f"- {title} (${price})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await utils.close()

if __name__ == "__main__":
    asyncio.run(test_shopify())




