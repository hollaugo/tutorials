# OpenAI Apps SDK Implementation Verification

**Date:** 2025-10-25
**Reference:** https://developers.openai.com/apps-sdk/build/custom-ux

## Critical Fix Applied

### Issue: Excessive Re-renders on Global Events

**Previous Implementation:**
```typescript
const handleSetGlobal = (event: CustomEvent) => {
  onChange(); // Always trigger re-render when event fires
};
```

**Problem:** This caused the component to re-render on **every** `openai:set_globals` event, even when the specific key being watched (like `toolOutput`) hadn't changed. This could explain why:
- Loading screen persisted longer than necessary
- Components might not have been syncing properly with data updates
- Unnecessary renders could cause performance issues

**Official Pattern (from OpenAI docs):**
```typescript
const handleSetGlobal = (event: SetGlobalsEvent) => {
  const value = event.detail.globals[key];
  if (value === undefined) return;  // Only trigger onChange if key changed
  onChange();
};
```

**Our Fixed Implementation:**
```typescript
const handleSetGlobal = (event: CustomEvent) => {
  // Only trigger onChange if this specific key changed
  // This matches the official OpenAI Apps SDK pattern
  if (event.detail?.globals?.[key] !== undefined) {
    onChange();
  }
};
```

**Impact:**
- Components now only re-render when their specific watched data changes
- More efficient reactivity
- Should resolve the loading state persistence issue

---

## Implementation Verification Checklist

Based on official OpenAI Apps SDK documentation:

### ✅ Core Hook Implementation (hooks.ts)

- [x] **useOpenAiGlobal** - Uses `useSyncExternalStore` correctly
  - [x] Subscribes to `"openai:set_globals"` event with passive listener
  - [x] Only triggers `onChange` when specific key changes (FIXED)
  - [x] Returns cleanup function to remove event listener
  - [x] Provides client snapshot via `() => window.openai[key]`
  - [x] Provides server-side snapshot via `() => null`
  - [x] Proper TypeScript typing with `keyof OpenAiGlobals`

- [x] **useToolOutput** - Accesses latest MCP server response
  - Pattern: `useOpenAiGlobal("toolOutput")`
  - Returns typed data or null

- [x] **useTheme** - Detects light/dark mode
  - Pattern: `useOpenAiGlobal("theme")` with fallback to "light"

- [x] **useWidgetState** - Manages persistent state
  - [x] Initializes from `window.openai.widgetState`
  - [x] Syncs React state with host-persisted data
  - [x] Calls `window.openai.setWidgetState()` to persist changes
  - [x] Supports function updaters and default values

- [x] **useCallTool** - Invokes MCP tools from component
  - Pattern: `window.openai.callTool(name, args)`
  - Returns Promise<CallToolResponse>

- [x] **useSendFollowUpMessage** - Inserts chat messages
  - Pattern: `window.openai.sendFollowUpMessage({ prompt })`

### ✅ TypeScript Types (types.ts)

- [x] `Theme` type: "light" | "dark"
- [x] `DisplayMode` type: "pip" | "inline" | "fullscreen"
- [x] `OpenAiGlobals` interface with all properties:
  - theme, userAgent, locale, maxHeight, displayMode
  - safeArea, toolInput, toolOutput, toolResponseMetadata
  - widgetState
- [x] `OpenAiAPI` interface with all methods:
  - callTool, sendFollowUpMessage, openExternal
  - requestDisplayMode, setWidgetState
- [x] `SetGlobalsEvent` class extending CustomEvent
- [x] Global Window interface augmentation
- [x] WindowEventMap augmentation for event types

### ✅ Component Implementation (ProductCarouselComponent.tsx)

- [x] **Data Loading:**
  - Uses `useToolOutput<ProductCarouselOutput>()`
  - Implements loading state: `const isLoading = !toolOutput;`
  - Shows loading spinner with proper styling

- [x] **Theme Support:**
  - Uses `useTheme()` hook
  - Applies theme-appropriate colors throughout
  - Dark mode: `#122017` background, `#1a1a1a` cards
  - Light mode: `#f6f8f7` background, `#ffffff` cards

- [x] **Widget State Persistence:**
  - Uses `useWidgetState<ProductCarouselWidgetState>({ favorites: [] })`
  - Persists favorite products across sessions
  - Updates via `setWidgetState({ ...widgetState, favorites: newFavorites })`

- [x] **Interactive Features:**
  - Card clicks call `viewCardFullscreen()`:
    - Requests fullscreen: `window.openai.requestDisplayMode({ mode: "fullscreen" })`
    - Calls tool: `callTool("show-product-detail", { product_title })`
  - Cart button with `event.stopPropagation()` to prevent card click
  - Hover detection: `window.openai?.userAgent?.capabilities?.hover`

- [x] **Responsive Design:**
  - Max width: 1280px
  - Horizontal scroll with snap points
  - Mobile-friendly touch scrolling
  - Hidden scrollbars

- [x] **Component Mounting:**
  - Mounts to `#shopify-carousel-root`
  - Uses React 18's `createRoot()`
  - No polling - relies on event-driven updates

### ✅ Server-Side Pattern (server.py)

- [x] Returns `structuredContent` that maps to `window.openai.toolOutput`
- [x] Embeds widget via `EmbeddedResource` with:
  - `uri: "ui://widget/product-carousel.html"`
  - `mimeType: "text/html+skybridge"`
  - Bundled JavaScript in `<script>` tag
- [x] Includes metadata:
  - `"openai.com/widget"`: widget resource
  - `"openai/widgetAccessible": True`
  - `"openai/resultCanProduceWidget": True`

---

## Key Differences from Documentation

### 1. TypeScript Typing
**Docs:** Use exact type from generic parameter
```typescript
export function useOpenAiGlobal<K extends keyof OpenAiGlobals>(
  key: K
): OpenAiGlobals[K]
```

**Our Implementation:** Added null fallback for safety
```typescript
): OpenAiGlobals[K] | null
```

**Rationale:** Accounts for cases where window.openai might not be available yet (SSR, initial load).

### 2. Event Type Checking
**Docs:** Use typed SetGlobalsEvent
```typescript
const handleSetGlobal = (event: SetGlobalsEvent) => {
  const value = event.detail.globals[key];
```

**Our Implementation:** Use generic CustomEvent with optional chaining
```typescript
const handleSetGlobal = (event: CustomEvent) => {
  if (event.detail?.globals?.[key] !== undefined) {
```

**Rationale:** More defensive programming - handles edge cases where event structure might vary.

---

## Testing Checklist

To verify the fixes work correctly:

- [ ] **Initial Load:** Products should render immediately without requiring refresh
- [ ] **Loading State:** Should show spinner only while toolOutput is null
- [ ] **Theme Switching:** Component should update colors when theme changes
- [ ] **Card Clicks:** Should request fullscreen and show product detail
- [ ] **Cart Button:** Should show alert and not trigger card click
- [ ] **Favorites:** Should persist across tool calls (test by favoriting, then searching again)
- [ ] **Scroll Navigation:** Arrow buttons should scroll carousel smoothly
- [ ] **Product Count:** Should show "Showing N products" correctly

---

## What Changed in This Fix

**File:** `/Users/uosuji/prompt-circle-phoenix/tutorials/shopify-store-chatgpt-app/web/src/hooks.ts`

**Lines 15-45:** Updated `useOpenAiGlobal` function

**Before:**
- Triggered re-render on every `set_globals` event
- No filtering by key
- Could cause excessive renders

**After:**
- Only triggers re-render when specific key has a value in event.detail.globals
- Matches official OpenAI Apps SDK pattern
- More efficient and predictable

**TypeScript Improvements:**
- Changed generic constraint from `K extends string` to `K extends keyof OpenAiGlobals`
- Changed return type from `any` to `OpenAiGlobals[K] | null`
- Added proper imports for `OpenAiGlobals` type

---

## Expected Behavior After Fix

1. **Component loads immediately** when tool returns data (no refresh needed)
2. **Loading spinner** shows only during initial data fetch
3. **Interactions work** on first render (cards clickable, cart button functional)
4. **Re-renders are minimal** - only when relevant data changes
5. **Console logs** should show:
   ```
   ProductCarouselApp render: { toolOutput: {...}, productsCount: 10, ... }
   Loading state: false Products: 10
   ```

---

## Resources

- **Official Docs:** https://developers.openai.com/apps-sdk/build/custom-ux
- **API Reference:** https://developers.openai.com/apps-sdk/reference
- **Design Guidelines:** https://developers.openai.com/apps-sdk/plan/components
- **This Implementation:** /Users/uosuji/prompt-circle-phoenix/tutorials/shopify-store-chatgpt-app/

---

## Summary

The critical fix was updating the `useOpenAiGlobal` hook to match the official OpenAI Apps SDK pattern. Instead of triggering re-renders on every global event, we now only trigger when the specific key being watched has changed. This should resolve the loading persistence issue and improve overall component performance.

The implementation now fully aligns with the official documentation and follows all recommended patterns for:
- Event-driven reactivity with useSyncExternalStore
- Proper TypeScript typing
- Theme support
- Display mode APIs
- Widget state persistence
- Tool invocation from components
