"""Test script to check numeric ID acceptance."""
import asyncio
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from shopify_utils import ShopifyUtils

async def test_numeric_ids():
    print("=" * 60)
    print("Testing Numeric IDs in GraphQL")
    print("=" * 60)

    shopify = ShopifyUtils()
    
    try:
        # 1. Search for a product to get a real GID
        products = await shopify.search_products("soap", limit=1)
        if not products:
            print("❌ No products found to test with.")
            return

        real_gid = products[0]["variants"][0]["id"]
        print(f"ℹ️  Real GID: {real_gid}")
        
        # Extract numeric ID
        numeric_id = real_gid.split("/")[-1]
        print(f"ℹ️  Numeric ID: {numeric_id}")

        # 2. Test get_cart_items_details with Numeric ID
        print("\nTesting get_cart_items_details with Numeric ID...")
        details = await shopify.get_cart_items_details([numeric_id])
        
        if details:
            print(f"✅ Success! Got details for numeric ID: {details[0]['title']}")
        else:
            print("❌ Failed. GraphQL 'nodes' query likely requires GIDs.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    finally:
        await shopify.close()

if __name__ == "__main__":
    asyncio.run(test_numeric_ids())
