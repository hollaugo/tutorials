
import asyncio
import os
import json
from dotenv import load_dotenv
from shopify_utils import ShopifyUtils

load_dotenv()

async def main():
    utils = ShopifyUtils()
    try:
        print("Searching for 'allKidz'...")
        products = await utils.search_products("allKidz", limit=1)
        if not products:
            print("No products found.")
            return

        product_id = products[0]["id"]
        print(f"Found product: {products[0]['title']} ({product_id})")

        print("Fetching details...")
        # We need to access the private method or copy the query to see raw data
        # But get_product_details returns transformed data.
        # Let's modify the utils temporarily or just trust the transformed data first?
        # No, I want to see the RAW response to see what metafields are actually there.
        
        # Let's manually run the query here to see raw output
        
        session = utils.session or io_session()
        
        # I'll just use the public method first to see what it returns
        details = await utils.get_product_details(product_id)
        print("\n--- Transformed Data ---")
        print(json.dumps(details, indent=2))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await utils.close()

def io_session():
    import aiohttp
    return aiohttp.ClientSession()

if __name__ == "__main__":
    asyncio.run(main())
