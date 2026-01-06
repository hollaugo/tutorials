# Critical Rendering Fix - Products Now Display!

## 🐛 Root Causes Found

### 1. Hook Implementation Was Wrong
**Problem:** Using `useState` + `useEffect` doesn't properly subscribe to `window.openai` changes

**Solution:** Use `useSyncExternalStore` with event listener for `"openai:set_globals"`

```typescript
// ❌ WRONG (old way)
function useOpenAiGlobal<T>(key: string): T | null {
  const [value, setValue] = useState<T | null>(() => {
    return window.openai?.[key] ?? null;
  });

  useEffect(() => {
    setValue(window.openai?.[key] ?? null);
  }, [key]);

  return value;
}

// ✅ CORRECT (fpl-deepagent way)
function useOpenAiGlobal<K extends string>(key: K): any {
  return useSyncExternalStore(
    (onChange) => {
      const handleSetGlobal = (event: CustomEvent) => {
        const globals = (event as any).detail.globals;
        if (globals?.[key] !== undefined) {
          onChange(); // Trigger re-render
        }
      };

      window.addEventListener("openai:set_globals", handleSetGlobal, {
        passive: true,
      });

      return () => {
        window.removeEventListener("openai:set_globals", handleSetGlobal);
      };
    },
    () => window.openai?.[key] // Get current value
  );
}
```

### 2. Excessive Height Issue
**Problem:** `minHeight: "100vh"` caused super long vertical scroll

**Solution:** Remove all height constraints, let content determine height

```typescript
// ❌ WRONG
<div style={{
  padding: "20px 16px",
  minHeight: "100vh",  // <-- This causes excessive height!
  display: "flex",
  justifyContent: "center",
}}>

// ✅ CORRECT
<div style={{
  padding: "20px 16px",  // Just padding, no height
}}>
```

### 3. Over-Complicated Mounting
**Problem:** Polling for `window.openai` with timeouts

**Solution:** Just mount immediately like fpl-deepagent

```typescript
// ❌ WRONG (polling)
function mountComponent() {
  const root = document.getElementById("shopify-carousel-root");
  if (root) {
    createRoot(root).render(<ProductCarouselApp />);
  }
}

if (window.openai) {
  mountComponent();
} else {
  let attempts = 0;
  const checkInterval = setInterval(() => {
    attempts++;
    if (window.openai || attempts > 50) {
      clearInterval(checkInterval);
      mountComponent();
    }
  }, 100);
}

// ✅ CORRECT (simple)
const root = document.getElementById("shopify-carousel-root");
if (root) {
  createRoot(root).render(<ProductCarouselApp />);
}
```

The hooks handle waiting for data via `useSyncExternalStore`!

### 4. Unnecessary Loading State
**Problem:** Loading state with delays caused flashing

**Solution:** Remove it - data loads fast enough, hooks handle it

```typescript
// ❌ WRONG
const [isLoading, setIsLoading] = useState(true);
useEffect(() => {
  if (toolOutput) {
    setTimeout(() => setIsLoading(false), 300);
  }
}, [toolOutput]);

if (isLoading) return <Spinner />;

// ✅ CORRECT
// Just render - useSyncExternalStore handles reactivity
const products = toolOutput?.products || [];
```

## 🔧 Files Changed

### hooks.ts - CRITICAL FIX
```typescript
import { useSyncExternalStore } from "react";

export function useOpenAiGlobal<K extends string>(key: K): any {
  return useSyncExternalStore(
    (onChange) => {
      const handleSetGlobal = (event: CustomEvent) => {
        const globals = (event as any).detail.globals;
        if (globals?.[key] !== undefined) {
          onChange();
        }
      };

      window.addEventListener("openai:set_globals", handleSetGlobal, {
        passive: true,
      });

      return () => {
        window.removeEventListener("openai:set_globals", handleSetGlobal);
      };
    },
    () => window.openai?.[key]
  );
}
```

### ProductCarouselComponent.tsx
**Removed:**
- ❌ `isLoading` state
- ❌ Loading spinner component
- ❌ `minHeight: "100vh"`
- ❌ Polling logic in mounting

**Kept:**
- ✅ Simple mounting: `createRoot(root).render(<App />)`
- ✅ Constrained width: `maxWidth: 1280px`
- ✅ Scroll snap behavior
- ✅ Debug logging

## 🎯 How It Works Now

### Data Flow (Correct)

1. **Server returns data:**
   ```python
   return types.ServerResult(
       types.CallToolResult(
           content=[...],
           structuredContent={"products": [...]},  # Data here
           _meta={...}
       )
   )
   ```

2. **OpenAI SDK sets window.openai:**
   ```javascript
   window.openai = {
       toolOutput: {"products": [...]},  // From structuredContent
       theme: "light",
       // ...
   };
   ```

3. **OpenAI SDK dispatches event:**
   ```javascript
   window.dispatchEvent(new CustomEvent("openai:set_globals", {
       detail: { globals: window.openai }
   }));
   ```

4. **useSyncExternalStore catches it:**
   ```typescript
   // Event listener triggers onChange()
   handleSetGlobal = (event) => {
       onChange();  // Component re-renders!
   };
   ```

5. **Component reads fresh data:**
   ```typescript
   const toolOutput = useToolOutput();  // Gets latest from window.openai
   const products = toolOutput?.products || [];
   ```

6. **Products render!** 🎉

## 🔍 Debugging

### Check if data is present:
```javascript
// In browser console
console.log(window.openai.toolOutput);
// Should show: {products: [...]}
```

### Check if component mounted:
```javascript
// Should see in console:
// "Mounting ProductCarouselApp, window.openai: {...}"
// "ProductCarouselApp render: {toolOutput: {...}, productsCount: 10}"
```

### Check if event fires:
```javascript
window.addEventListener("openai:set_globals", (e) => {
  console.log("openai:set_globals fired:", e.detail.globals);
});
```

## ✅ Expected Behavior Now

1. Tool called with `query: "gut health supplements"`
2. Server returns `structuredContent: {products: [10 items]}`
3. OpenAI sets `window.openai.toolOutput = {products: [...]}`
4. Event `"openai:set_globals"` fires
5. `useSyncExternalStore` triggers re-render
6. Component renders 10 product cards
7. Carousel shows with constrained width (1280px max)

## 📊 Before vs After

### Before (Broken)
- ❌ Products don't render
- ❌ Super long vertical scroll
- ❌ Loading spinner shows indefinitely
- ❌ Empty state with debug panel

### After (Fixed)
- ✅ Products render immediately
- ✅ Proper constrained height
- ✅ No loading flash
- ✅ Carousel scrolls horizontally within 1280px

## 🚀 Key Takeaway

**The OpenAI Apps SDK uses events, not props!**

- Don't poll for `window.openai`
- Don't use `useState` + `useEffect` for window.openai values
- **DO use `useSyncExternalStore`** with `"openai:set_globals"` event
- Follow the **exact pattern from fpl-deepagent**

## 📁 Reference Files

Pattern copied from:
- `/Users/uosuji/prompt-circle-phoenix/tutorials/fpl-deepagent/web/src/hooks.ts`
- `/Users/uosuji/prompt-circle-phoenix/tutorials/fpl-deepagent/web/src/PlayerListComponent.tsx`

These are the official working examples that render correctly in ChatGPT!
