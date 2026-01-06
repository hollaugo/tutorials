"""Test the essential oils query that was failing."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from shopify_utils import ShopifyUtils
import aiohttp


async def test_essential_oils_query():
    """Test searching for 'essential oils'."""
    print("=" * 60)
    print("Testing 'essential oils' Query")
    print("=" * 60)

    shopify_utils = ShopifyUtils(timeout_seconds=25)

    try:
        async with aiohttp.ClientSession() as session:
            # Test the comprehensive search
            print("\n🔍 Searching for 'essential oils'...")
            products = await shopify_utils.search_products(
                "essential oils",
                limit=10,
                session=session
            )

            print(f"\n✅ Found {len(products)} products")

            if len(products) > 0:
                print("\n📦 Products matching 'essential oils':")
                for i, product in enumerate(products, 1):
                    print(f"\n{i}. {product['title']}")
                    print(f"   Price: {product['currency']} {product['price']}")
                    print(f"   Vendor: {product.get('vendor', 'N/A')}")
                    print(f"   Tags: {', '.join(product.get('tags', []))[:100]}")
                    print(f"   Description: {product.get('description', '')[:100]}...")
                    print(f"   Collections: {', '.join(product.get('collections', []))}")
            else:
                print("\n⚠️  No products found")
                print("\nLet's check what products exist in the store:")
                all_products = await shopify_utils.get_products(limit=20, session=session)
                print(f"\nTotal products in store: {len(all_products)}")
                print("\nFirst 10 products:")
                for i, p in enumerate(all_products[:10], 1):
                    print(f"{i}. {p['title']}")
                    print(f"   Tags: {', '.join(p.get('tags', []))[:80]}")

            # Test other search terms
            print("\n" + "=" * 60)
            print("Testing other search terms:")
            print("=" * 60)

            test_queries = ["oil", "essential", "aromatherapy", "wellness", "soap"]
            for query in test_queries:
                results = await shopify_utils.search_products(query, limit=5, session=session)
                print(f"\n'{query}': {len(results)} products")
                for p in results[:3]:
                    print(f"  - {p['title']}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await shopify_utils.close()


if __name__ == "__main__":
    asyncio.run(test_essential_oils_query())
