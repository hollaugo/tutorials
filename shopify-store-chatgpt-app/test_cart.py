"""Test script for Shopping Cart feature."""
import asyncio
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from shopify_utils import ShopifyUtils
from server import ManageCartInput, CartItem

async def test_cart_feature():
    print("=" * 60)
    print("Testing Shopping Cart Feature")
    print("=" * 60)

    shopify = ShopifyUtils()
    
    try:
        # Test 1: Generate Checkout URL
        print("\n1. Testing generate_checkout_url...")
        items = [
            {"variant_id": "gid://shopify/ProductVariant/123456789", "quantity": 1},
            {"variant_id": "987654321", "quantity": 2}
        ]
        url = shopify.generate_checkout_url(items)
        print(f"   ✅ Generated URL: {url}")
        
        expected_part = "/cart/123456789:1,987654321:2"
        if expected_part in url:
            print("   ✅ URL format is correct")
        else:
            print(f"   ❌ URL format incorrect. Expected to contain: {expected_part}")

        # Test 2: Validate Input Models
        print("\n2. Testing Input Models...")
        try:
            input_data = {
                "action": "add",
                "items": [
                    {"variant_id": "gid://shopify/ProductVariant/111", "quantity": 1}
                ]
            }
            model = ManageCartInput(**input_data)
            print(f"   ✅ Model validation successful: {model.action}")
        except Exception as e:
            print(f"   ❌ Model validation failed: {e}")

        # Test 3: Fetch Cart Item Details (New)
        print("\n3. Testing get_cart_items_details...")
        # We need a real variant ID for this to work. 
        # Let's first search for a product to get a valid ID.
        products = await shopify.search_products("soap", limit=1)
        if products and products[0].get("variants"):
            variant_id = products[0]["variants"][0]["id"]
            print(f"   ℹ️  Using variant ID: {variant_id}")
            
            details = await shopify.get_cart_items_details([variant_id])
            if details:
                print(f"   ✅ Fetched details for {len(details)} item(s)")
                print(f"   📝 Title: {details[0].get('title')}")
                print(f"   💰 Price: {details[0].get('price')}")
                if details[0].get("image_url"):
                    print("   🖼️  Image URL found")
                else:
                    print("   ⚠️  No image URL found")
            else:
                print("   ❌ Failed to fetch details (returned empty list)")
        else:
            print("   ⚠️  Skipping detail test: No products found to test with")

        print("\n" + "=" * 60)
        print("✅ Cart tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    finally:
        await shopify.close()

if __name__ == "__main__":
    asyncio.run(test_cart_feature())
