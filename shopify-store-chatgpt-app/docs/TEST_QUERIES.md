# Shopify Store ChatGPT App - Test Queries

This document provides example queries to test the Shopify Store ChatGPT App functionality.

## 🛍️ Product Carousel Queries

### **Basic Product Display**
```
"Show me your products"
"Display your product catalog"
"What products do you have?"
"Show me your store inventory"
```

### **Search by Category**
```
"Show me wellness products"
"Display supplements"
"Find organic products"
"Show me skincare items"
"Display vitamins and supplements"
```

### **Search by Price Range**
```
"Show me products under $20"
"Display items under $50"
"Find products under $100"
"Show me affordable options"
```

### **Search by Brand/Vendor**
```
"Show me products from Wellness Co"
"Display items by Nature's Best"
"Find products from Organic Life"
"Show me Wellness Co products"
```

### **Search by Keywords**
```
"Show me vitamin products"
"Find organic supplements"
"Display natural skincare"
"Show me protein powders"
"Find herbal teas"
```

### **Collection-based Search**
```
"Show me best sellers"
"Display new arrivals"
"Find featured products"
"Show me seasonal items"
```

## 🔍 Product Detail Queries

### **Specific Product Details**
```
"Show me the vitamin D3 gummies product details"
"Get details for the organic chamomile tea"
"Show me the natural mineral sunscreen details"
"Display the raw manuka honey product info"
```

### **Product by Title Search**
```
"Show details for Vitamin D3 Gummies"
"Get info on Organic Chamomile Tea"
"Show me details for Natural Mineral Sunscreen"
"Display Raw Manuka Honey details"
```

### **Product by ID (if known)**
```
"Show product details for gid://shopify/Product/123"
"Get details for product ID gid://shopify/Product/456"
```

## 🏷️ Advanced Search Queries

### **Ingredient-based Search**
```
"Show me products with vitamin D"
"Find items with organic ingredients"
"Display products containing chamomile"
"Show me items with natural ingredients"
```

### **Tag-based Search**
```
"Show me products tagged as organic"
"Find items tagged as supplements"
"Display products tagged as wellness"
"Show me items tagged as natural"
```

### **Combined Filters**
```
"Show me organic supplements under $30"
"Find wellness products from Wellness Co"
"Display natural skincare under $50"
"Show me vitamin products under $25"
```

## 🎨 UI Component Testing

### **Carousel Navigation**
```
"Show me more products"
"Display the next set of products"
"Show me different products"
"Load more items"
```

### **Product Interaction**
```
"Add this to my favorites"
"Show me more details about this product"
"Tell me more about the ingredients"
"Show me the variants for this product"
```

## 🔧 Technical Testing

### **Error Handling**
```
"Show me products from a non-existent brand"
"Find products with invalid filters"
"Display products with empty search"
```

### **Edge Cases**
```
"Show me all products" (large dataset)
"Find products with no images"
"Display products with no variants"
"Show me out-of-stock products"
```

## 📱 Mobile Testing

### **Responsive Design**
```
"Show me products on mobile"
"Display the carousel on tablet"
"Find products on small screen"
```

## 🌙 Theme Testing

### **Dark/Light Mode**
```
"Show me products in dark mode"
"Display carousel in light theme"
"Find products with dark background"
```

## 🚀 Performance Testing

### **Large Datasets**
```
"Show me all products" (if store has many products)
"Display every item in your catalog"
"Find all products in your store"
```

## 📊 Analytics Testing

### **User Interaction**
```
"Show me what I've favorited"
"Display my recent product views"
"Find products I've interacted with"
```

## 🎯 Expected Behaviors

### **Carousel Component**
- ✅ Horizontal scrolling with hidden scrollbar
- ✅ Product cards with square images
- ✅ Hover effects and transitions
- ✅ Navigation arrows (left/right)
- ✅ Responsive card sizing (264-288px)
- ✅ Favorites functionality
- ✅ "Add to Cart" button calls product detail

### **Product Detail Component**
- ✅ Image gallery with thumbnails
- ✅ Variant selector dropdowns
- ✅ Ingredients section (from metafields)
- ✅ Collections as badge pills
- ✅ Inventory status indicator
- ✅ Expandable description
- ✅ Vendor and SKU information

### **Search & Filter**
- ✅ Text search across title, description, vendor, tags
- ✅ Collection filtering
- ✅ Price range filtering
- ✅ Vendor/brand filtering
- ✅ Tag-based filtering

## 🐛 Troubleshooting

### **Common Issues**
- **No products found**: Check Shopify API credentials
- **UI not loading**: Ensure React components are built
- **Search not working**: Verify GraphQL queries in shopify_utils.py
- **Images not displaying**: Check image URLs in Shopify

### **Debug Commands**
```bash
# Test API connection
uv run python shopify_utils.py

# Test specific product
uv run python shopify_utils.py product "gid://shopify/Product/123"

# Search products
uv run python shopify_utils.py search "vitamin"

# List collections
uv run python shopify_utils.py collections
```

## 📈 Success Metrics

- ✅ Products load within 2 seconds
- ✅ UI renders correctly in ChatGPT
- ✅ Search returns relevant results
- ✅ Product details show complete information
- ✅ Carousel scrolls smoothly
- ✅ Hover effects work on supported devices
- ✅ Mobile responsive design
- ✅ Dark/light theme support
