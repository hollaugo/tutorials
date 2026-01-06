
import os
import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from pydantic import BaseModel, Field

from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class ComparisonAttribute(BaseModel):
    name: str = Field(..., description="Name of the attribute (e.g., 'Dosage', 'Flavor', 'Age Range')")
    values: Dict[str, str] = Field(..., description="Map of product ID to attribute value")

class ComparisonResult(BaseModel):
    summary: str = Field(..., description="Brief summary of the key differences and similarities")
    common_features: List[str] = Field(..., description="List of features shared by all products")
    attributes: List[ComparisonAttribute] = Field(..., description="List of attributes for detailed comparison")
    recommendation: Optional[str] = Field(None, description="Optional recommendation based on use case")

async def extract_comparison_data(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Uses Gemini to extract structured comparison data from product details.
    """
    # Re-check key in case it was loaded late
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️ GOOGLE_API_KEY not found. Returning empty comparison.")
        return {}
    
    # Ensure configured
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    try:
        model = genai.GenerativeModel("gemini-3-pro-preview")
        
        # Prepare prompt
        products_context = []
        for p in products:
            products_context.append({
                "id": p.get("id"),
                "title": p.get("title"),
                "description": p.get("description"),
                "price": p.get("price"),
                "vendor": p.get("vendor"),
                "ingredients": p.get("ingredients")
            })
            
        prompt = f"""
        Analyze these products and generate a structured comparison in JSON format.
        
        Guidelines:
        1. **Avoid Redundancy**: Do not create separate attributes for things that are essentially the same (e.g., "Ingredients" vs "Components"). Merge them.
        2. **Normalize Names**: Use standard attribute names like "Scent", "Weight", "Skin Type", "Key Ingredients".
        3. **Concise Values**: Keep attribute values short and direct.
        
        The JSON must follow this structure:
        {{
            "summary": "Brief summary of key differences",
            "common_features": ["feature1", "feature2"],
            "attributes": [
                {{
                    "name": "Attribute Name (e.g. Scent)",
                    "values": {{ "product_id": "value" }}
                }}
            ],
            "recommendation": "Optional recommendation"
        }}
        
        Products:
        {json.dumps(products_context, indent=2)}
        """

        # Generate structured content
        print(f"🤖 Sending request to Gemini for {len(products)} products...")
        result = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        print("🤖 Gemini response received")
        return json.loads(result.text)

    except Exception as e:
        print(f"❌ LLM Extraction Error: {e}")
        import traceback
        traceback.print_exc()
        return {}
