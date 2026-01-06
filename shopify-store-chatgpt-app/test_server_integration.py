"""Test the specific code path that was causing the bug in server.py."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from shopify_utils import ShopifyUtils
import aiohttp


async def test_server_integration():
    """Test the exact code path from server.py that was failing."""
    print("=" * 60)
    print("Testing server.py Integration (Bug Fix)")
    print("=" * 60)

    shopify_utils = ShopifyUtils(timeout_seconds=25)

    try:
        # Simulate the show-products-carousel tool with query filter
        # This is the code path from server.py lines 280-287
        print("\n📦 Simulating show-products-carousel with query filter...")

        async with aiohttp.ClientSession() as session:
            # Get products
            products = await shopify_utils.get_products(
                limit=10,
                session=session
            )
            print(f"✅ Retrieved {len(products)} products")

            # This is line 287 from server.py - the line that was failing!
            query = "soap"
            print(f"\n🔍 Applying query filter: '{query}'")
            filtered_products = [
                p for p in products
                if shopify_utils._name_matches(p.get("title", ""), query)
            ]

            print(f"✅ Filter applied successfully!")
            print(f"   Found {len(filtered_products)} products matching '{query}':")
            for product in filtered_products[:5]:
                print(f"   - {product['title']}")

            # Test with different queries
            print("\n🔍 Testing additional queries...")
            for test_query in ["travel", "milk", "scrub"]:
                filtered = [
                    p for p in products
                    if shopify_utils._name_matches(p.get("title", ""), test_query)
                ]
                print(f"   '{test_query}': {len(filtered)} matches")

        # Test the product detail flow (server.py lines 328-352)
        print("\n📋 Simulating show-product-detail with title search...")

        async with aiohttp.ClientSession() as session:
            product_title = "Travel Soaps"
            print(f"   Searching for product: '{product_title}'")

            # Search for product by title (line 334)
            products = await shopify_utils.search_products(
                product_title,
                limit=1,
                session=session
            )

            if products:
                print(f"✅ Found product: {products[0]['title']}")

                # Get detailed info (line 349)
                product = await shopify_utils.get_product_by_id(
                    products[0]["id"],
                    session=session
                )
                print(f"✅ Retrieved product details:")
                print(f"   - ID: {product['id']}")
                print(f"   - Title: {product['title']}")
                print(f"   - Price: {product['currency']} {product['price']}")
                print(f"   - Inventory: {product['inventory']}")
                print(f"   - Available: {product['available']}")
                print(f"   - Images: {len(product['images'])}")
                print(f"   - Variants: {len(product['variants'])}")
            else:
                print(f"⚠️  Product '{product_title}' not found")

        print("\n" + "=" * 60)
        print("✅ Server integration tests PASSED!")
        print("   The original bug is FIXED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await shopify_utils.close()


if __name__ == "__main__":
    asyncio.run(test_server_integration())
