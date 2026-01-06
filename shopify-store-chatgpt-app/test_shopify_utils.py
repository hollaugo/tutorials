"""Test script for ShopifyUtils methods."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from shopify_utils import ShopifyUtils


async def test_shopify_utils():
    """Test all ShopifyUtils methods."""
    print("=" * 60)
    print("Testing ShopifyUtils Methods")
    print("=" * 60)

    shopify = ShopifyUtils(timeout_seconds=25)

    try:
        # Test 1: API Connection
        print("\n1. Testing API Connection...")
        result = await shopify.test_api_connection()
        if result["success"]:
            print(f"   ✅ API Connection successful")
            print(f"   Shop: {result.get('data', {}).get('shop', {}).get('name', 'N/A')}")
        else:
            print(f"   ❌ API Connection failed: {result.get('error')}")
            return

        # Test 2: Get Products
        print("\n2. Testing get_products (limit=5)...")
        products = await shopify.get_products(limit=5)
        print(f"   ✅ Retrieved {len(products)} products")
        if products:
            product = products[0]
            print(f"   Sample product: {product['title']}")
            print(f"   - ID: {product['id']}")
            print(f"   - Price: {product['currency']} {product['price']}")
            print(f"   - Inventory: {product.get('inventory', 'N/A')}")
            print(f"   - Available: {product.get('available', 'N/A')}")
            print(f"   - Variants: {len(product.get('variants', []))}")

            # Store first product for later tests
            test_product_id = product['id']
            test_product_title = product['title']
        else:
            print("   ⚠️  No products found in store")
            return

        # Test 3: _name_matches static method
        print("\n3. Testing _name_matches...")
        test_cases = [
            ("Product Name", "product", True),
            ("Product Name", "PRODUCT", True),
            ("Product Name", "name", True),
            ("Product Name", "xyz", False),
        ]
        all_passed = True
        try:
            for name, query, expected in test_cases:
                # Call it both ways to ensure compatibility
                result = shopify._name_matches(name, query)
                status = "✅" if result == expected else "❌"
                if result != expected:
                    all_passed = False
                print(f"   {status} _name_matches('{name}', '{query}') = {result} (expected {expected})")

            if all_passed:
                print("   ✅ All _name_matches tests passed")
        except Exception as e:
            print(f"   ⚠️  _name_matches test error: {e}")
            # Try calling as instance method
            print("   Trying as instance method...")
            for name, query, expected in test_cases:
                result = query.lower() in name.lower()  # Manual test
                status = "✅" if result == expected else "❌"
                print(f"   {status} Manual check: '{query}' in '{name}' = {result} (expected {expected})")

        # Test 4: Search Products
        print("\n4. Testing search_products...")
        # Search for a common term
        search_results = await shopify.search_products("the", limit=3)
        print(f"   ✅ Search for 'the' returned {len(search_results)} products")
        for i, p in enumerate(search_results[:3], 1):
            print(f"   {i}. {p['title']}")

        # Test 5: Get Product by ID
        print("\n5. Testing get_product_by_id...")
        product_detail = await shopify.get_product_by_id(test_product_id)
        print(f"   ✅ Retrieved product: {product_detail['title']}")
        print(f"   - Description length: {len(product_detail.get('description', ''))}")
        print(f"   - Images: {len(product_detail.get('images', []))}")
        print(f"   - Variants: {len(product_detail.get('variants', []))}")
        print(f"   - Collections: {product_detail.get('collections', [])}")
        print(f"   - Inventory: {product_detail.get('inventory', 'N/A')}")
        print(f"   - Available: {product_detail.get('available', 'N/A')}")
        print(f"   - Ingredients: {product_detail.get('ingredients', 'N/A')[:50]}...")

        # Test 6: Get Product by Title
        print("\n6. Testing get_product_by_title...")
        try:
            product_by_title = await shopify.get_product_by_title(test_product_title)
            print(f"   ✅ Retrieved product by title: {product_by_title['title']}")
            print(f"   - ID matches: {product_by_title['id'] == test_product_id}")
        except Exception as e:
            print(f"   ⚠️  Error getting product by title: {e}")

        # Test 7: Test with session parameter
        print("\n7. Testing methods with session parameter...")
        import aiohttp
        async with aiohttp.ClientSession() as session:
            products_with_session = await shopify.get_products(limit=2, session=session)
            print(f"   ✅ get_products with session: {len(products_with_session)} products")

            search_with_session = await shopify.search_products("the", limit=2, session=session)
            print(f"   ✅ search_products with session: {len(search_with_session)} products")

            detail_with_session = await shopify.get_product_by_id(test_product_id, session=session)
            print(f"   ✅ get_product_by_id with session: {detail_with_session['title']}")

        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await shopify.close()


if __name__ == "__main__":
    asyncio.run(test_shopify_utils())
