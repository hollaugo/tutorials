"""Test searching for 'gut health supplements'."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from shopify_utils import ShopifyUtils
import aiohttp


async def test_gut_health_search():
    """Test searching for gut health supplements."""
    print("=" * 60)
    print("Testing 'gut health supplements' Search")
    print("=" * 60)

    shopify_utils = ShopifyUtils(timeout_seconds=25)

    try:
        async with aiohttp.ClientSession() as session:
            # Test the search
            print("\n🔍 Searching for 'gut health supplements'...")
            products = await shopify_utils.search_products(
                "gut health supplements",
                limit=20,
                session=session
            )

            print(f"✅ Found {len(products)} products\n")

            if len(products) > 0:
                for i, product in enumerate(products, 1):
                    print(f"{i}. {product['title']}")
                    print(f"   Tags: {', '.join(product.get('tags', []))}")
                    print(f"   Description preview: {product.get('description', '')[:100]}")
                    print()
            else:
                print("❌ No products found")
                print("\nLet's search for each word separately:")

                for word in ["gut", "health", "supplement", "probiotic", "digestive"]:
                    results = await shopify_utils.search_products(word, limit=20, session=session)
                    print(f"\n'{word}': {len(results)} products")
                    if results:
                        for p in results[:3]:
                            print(f"  - {p['title']}")
                            print(f"    Tags: {', '.join(p.get('tags', []))[:60]}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await shopify_utils.close()


if __name__ == "__main__":
    asyncio.run(test_gut_health_search())
