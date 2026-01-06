# Navigation and External Link Fixes

**Date:** 2025-10-25
**Issues Fixed:** Fullscreen navigation to detail view + External shop links

---

## 🔧 Changes Made

### 1. Fixed Fullscreen Navigation (Carousel → Detail View)

**Problem:**
- Clicking product card went to fullscreen **of the carousel** instead of detail view
- Was requesting fullscreen mode BEFORE calling the tool

**Root Cause:**
```typescript
// OLD (WRONG)
const viewCardFullscreen = async (product: any) => {
  await window.openai.requestDisplayMode({ mode: "fullscreen" }); // ❌ This made carousel fullscreen
  await viewProductDetails(product); // Tool called after
};
```

**Solution:**
```typescript
// NEW (CORRECT)
const viewCardFullscreen = async (product: any) => {
  console.log("Card clicked, calling show-product-detail tool:", product.title);
  // Call the tool directly - the tool result will trigger the appropriate display
  await viewProductDetails(product);
};
```

**Server-Side Addition:**
```python
# server.py - Added display mode preference in metadata
meta: Dict[str, Any] = {
    "openai.com/widget": widget_resource.model_dump(mode="json"),
    "openai/outputTemplate": widget.template_uri,
    # ... other meta fields
}

# Add fullscreen preference for product detail view
if widget.identifier == "show-product-detail":
    meta["openai/preferredDisplayMode"] = "fullscreen"
```

**Key Learning:**
- Let the **tool result** control display mode, not the calling component
- Use metadata hints (`openai/preferredDisplayMode`) to suggest display modes
- The SDK will handle the transition based on the tool's response

---

### 2. External Shop Links Configuration

**Problem:**
- "View on Shopify" button not appearing or not working

**Root Cause:**
Need to verify:
1. ✅ `SHOPIFY_SHOP_DOMAIN` is set in `.env`
2. ✅ Server passes `shopDomain` through `structuredContent`
3. ✅ Component receives and uses `shopDomain`

**Configuration Check:**

```bash
# 1. Check .env file
cat .env | grep SHOPIFY_SHOP_DOMAIN
# Should show: SHOPIFY_SHOP_DOMAIN=shop.opalwellness.ca
```

**Code Flow:**

```python
# server.py - Line 35
SHOPIFY_SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN", "")

# server.py - Line 384 (show-product-detail tool)
structured_content = {
    "id": product["id"],
    "title": product["title"],
    "handle": product.get("handle", ""),
    # ... other fields
    "shopDomain": SHOPIFY_SHOP_DOMAIN  # ✅ Passed to component
}
```

```typescript
// ProductDetailComponent.tsx - Line 428
{product.handle && product.shopDomain && (
  <button onClick={() => {
    const shopUrl = `https://${product.shopDomain}/products/${product.handle}`;

    if (window.openai?.openExternal) {
      window.openai.openExternal({ href: shopUrl });
    } else {
      window.open(shopUrl, '_blank');
    }
  }}>
    View on Shopify →
  </button>
)}
```

**Button Visibility Requirements:**
- ✅ `product.handle` must be present (product URL slug)
- ✅ `product.shopDomain` must be present (from environment variable)
- If either is missing, button won't render (graceful degradation)

---

## 🧪 Testing Guide

### Test 1: Fullscreen Navigation

**Steps:**
1. Start the MCP server: `python server.py`
2. In ChatGPT: "Show me gut health supplements"
3. Carousel should appear with products
4. Click on any product card
5. **Expected:** Switches to fullscreen mode showing **product detail view**
6. **Not:** Fullscreen of the carousel

**Console Logs to Look For:**
```
Card clicked, calling show-product-detail tool: Product Name
```

**What to Check:**
- ✅ Detail view loads (not carousel in fullscreen)
- ✅ Shows product images, variants, full description
- ✅ Different layout from carousel

---

### Test 2: External Shop Links

**Steps:**
1. From product detail view (after clicking a card)
2. Look for "View on Shopify →" button below "Add to Cart"
3. Click the button
4. **Expected:** Opens product page in browser at `https://shop.opalwellness.ca/products/{handle}`

**Console Logs to Look For:**
```
Opening Shopify product page: https://shop.opalwellness.ca/products/gut-health-probiotic-blend
```

**Troubleshooting If Button Doesn't Appear:**

```bash
# 1. Check environment variable is set
cd /Users/uosuji/prompt-circle-phoenix/tutorials/shopify-store-chatgpt-app
cat .env | grep SHOPIFY_SHOP_DOMAIN

# 2. Restart server to pick up environment changes
# Kill server (Ctrl+C) and restart:
python server.py

# 3. Check product has handle field
# In browser console when viewing product detail:
console.log(window.openai?.toolOutput)
# Should show: { id: "...", handle: "...", shopDomain: "shop.opalwellness.ca", ... }
```

---

## 🔍 Debugging Checklist

### If Fullscreen Shows Carousel (Not Detail):

- [ ] Check carousel component was rebuilt: `cd web && npm run build`
- [ ] Verify `viewCardFullscreen` function doesn't call `requestDisplayMode`
- [ ] Check server.py has `meta["openai/preferredDisplayMode"] = "fullscreen"`
- [ ] Look for tool call in console: `show-product-detail`
- [ ] Restart MCP server to pick up changes

### If "View on Shopify" Button Missing:

- [ ] Check `.env` has `SHOPIFY_SHOP_DOMAIN=shop.opalwellness.ca`
- [ ] Restart server after changing `.env`
- [ ] Check browser console for `window.openai.toolOutput.shopDomain`
- [ ] Check product has `handle` field in toolOutput
- [ ] Verify component was rebuilt: `cd web && npm run build`

### If Button Appears But Link Doesn't Work:

- [ ] Check browser console for click event logs
- [ ] Verify `window.openai.openExternal` exists
- [ ] Try the fallback: check if browser popup blocker is active
- [ ] Verify URL format: `https://shop.opalwellness.ca/products/{handle}`

---

## 📊 Expected Data Flow

### Carousel → Detail Navigation

```
1. User clicks product card in carousel
   ↓
2. Component calls: callTool("show-product-detail", { product_title: "..." })
   ↓
3. Server receives request
   ↓
4. Server fetches product details from Shopify
   ↓
5. Server returns CallToolResult with:
   - structuredContent: { id, title, handle, shopDomain, ... }
   - _meta: { "openai/preferredDisplayMode": "fullscreen", ... }
   ↓
6. ChatGPT SDK:
   - Switches to fullscreen mode (due to metadata hint)
   - Loads product-detail widget
   - Passes structuredContent as window.openai.toolOutput
   ↓
7. ProductDetailComponent renders with product data
```

### External Link Click

```
1. User clicks "View on Shopify →" button
   ↓
2. Component constructs URL: `https://${product.shopDomain}/products/${product.handle}`
   ↓
3. Component calls: window.openai.openExternal({ href: shopUrl })
   ↓
4. ChatGPT SDK opens URL in user's default browser
```

---

## 📝 Files Modified

### Backend
1. **server.py**
   - Line 429-430: Added `openai/preferredDisplayMode` metadata for detail view
   - Line 324: Added `shopDomain` to carousel structured content
   - Line 384: Added `shopDomain` to detail structured content

### Frontend
1. **web/src/ProductCarouselComponent.tsx**
   - Lines 90-94: Simplified `viewCardFullscreen` - removed premature displayMode request

2. **web/src/ProductDetailComponent.tsx**
   - Line 428: Added condition check for `shopDomain`
   - Line 432: Uses `product.shopDomain` from environment

### Configuration
1. **.env**
   - Added: `SHOPIFY_SHOP_DOMAIN=shop.opalwellness.ca`

2. **.env.example**
   - Documented `SHOPIFY_SHOP_DOMAIN` with comments

---

## ✅ Success Criteria

After these fixes, you should be able to:

1. ✅ Click product card in carousel → see **product detail view** in fullscreen
2. ✅ See "View on Shopify →" button in product detail
3. ✅ Click button → opens actual Shopify product page
4. ✅ Console logs show correct URLs and tool calls
5. ✅ No premature fullscreen requests for carousel

---

## 🎯 Next Steps

If everything works:
- Test with different products to verify handles are correct
- Verify URLs open to correct product pages
- Check that product detail shows all fields properly

If issues persist:
- Share console logs from browser
- Share server logs from terminal
- Check the debugging checklist above
