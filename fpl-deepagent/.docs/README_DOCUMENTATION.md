# FPL MCP Server Documentation Index

Complete technical documentation for understanding how web resources work in the FPL MCP Server.

## 📚 Documentation Structure

### 1. **WEB_RESOURCES_TECHNICAL_GUIDE.md** 
🔬 **Deep Technical Dive** (17,000+ words)

**For:** Engineers who need to understand every detail  
**Contains:**
- Complete architecture explanation with code snippets
- Phase-by-phase breakdown of resource loading
- MCP protocol integration details
- React component internals
- Runtime data flow analysis
- Performance optimization techniques
- Debugging guides
- Complete code examples

**Best for:**
- Understanding the complete system
- Learning how MCP + React integration works
- Debugging complex issues
- Contributing new features

---

### 2. **QUICK_REFERENCE_WEB_RESOURCES.md**
⚡ **Quick Reference Guide** (~5,000 words)

**For:** Developers who need quick answers  
**Contains:**
- Essential concepts in one-liners
- Lookup tables (URIs, hooks, files)
- Data flow diagram
- Code snippets for common tasks
- Development workflow
- Debugging checklist
- Common patterns

**Best for:**
- Quick lookups during development
- Finding the right file to edit
- Remembering API names
- Following established patterns

---

### 3. **WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md**
🎨 **Visual Architecture** (~4,000 words)

**For:** Visual learners and architects  
**Contains:**
- System architecture diagrams
- Bundle loading flow charts
- Request-response sequences
- Component lifecycle diagrams
- State persistence flows
- window.openai API structure

**Best for:**
- Understanding system at a glance
- Explaining to stakeholders
- Onboarding new developers
- System design discussions

---

### 4. **PROJECT_OVERVIEW.md**
🎯 **High-Level Overview**

**For:** Understanding the project's purpose  
**Contains:**
- What the project does
- Architecture philosophy
- Current features
- Usage examples
- Production readiness status

**Best for:**
- First-time project visitors
- Understanding project goals
- Getting started quickly

---

## 🎓 Learning Paths

### Path 1: New to the Project
1. Start with **PROJECT_OVERVIEW.md** (10 min)
2. Skim **WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md** (15 min)
3. Read **QUICK_REFERENCE_WEB_RESOURCES.md** (20 min)
4. Deep dive into **WEB_RESOURCES_TECHNICAL_GUIDE.md** sections as needed

### Path 2: Need to Add a Feature
1. Check **QUICK_REFERENCE_WEB_RESOURCES.md** → "🚀 Adding a New Widget"
2. Follow the 4-step process
3. Refer to **WEB_RESOURCES_TECHNICAL_GUIDE.md** → "Code Examples & Implementation" for details

### Path 3: Debugging an Issue
1. Check **QUICK_REFERENCE_WEB_RESOURCES.md** → "🐛 Debugging Checklist"
2. If unclear, see **WEB_RESOURCES_TECHNICAL_GUIDE.md** → "Debugging & Troubleshooting"
3. Use **WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md** to understand data flow

### Path 4: Understanding MCP Protocol
1. Read **WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md** → "MCP Request-Response Flow"
2. Deep dive into **WEB_RESOURCES_TECHNICAL_GUIDE.md** → "MCP Protocol Integration"
3. See code in **QUICK_REFERENCE_WEB_RESOURCES.md** → "Code Snippets"

### Path 5: Understanding React Integration
1. Read **WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md** → "React Component Lifecycle"
2. Study **WEB_RESOURCES_TECHNICAL_GUIDE.md** → "React Component Integration"
3. Check **QUICK_REFERENCE_WEB_RESOURCES.md** → "React Hooks" table

---

## 🔑 Key Questions Answered

### "How do React bundles get to ChatGPT?"
→ **WEB_RESOURCES_TECHNICAL_GUIDE.md** → Phase 2: Server Startup  
→ **WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md** → React Bundle Loading Flow

**Quick Answer:** 
1. Built with esbuild at development time
2. Loaded into Python memory at server startup
3. Embedded in HTML `<script>` tag
4. Sent in MCP response `_meta.openai.com/widget`
5. ChatGPT injects and executes

---

### "How does React access data from the server?"
→ **WEB_RESOURCES_TECHNICAL_GUIDE.md** → Phase 5: Browser-Side Rendering  
→ **WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md** → Data Flow: Server → React

**Quick Answer:**
```typescript
// Server sends structuredContent
structuredContent: {players: [...]}

// ChatGPT sets window.openai.toolOutput
window.openai.toolOutput = structuredContent

// React reads via hook
const data = useToolOutput<{players: Player[]}>()
```

---

### "How does state persist across re-renders?"
→ **WEB_RESOURCES_TECHNICAL_GUIDE.md** → React Component Integration → Widget State Hook  
→ **WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md** → State Persistence Flow

**Quick Answer:**
```typescript
const [state, setState] = useWidgetState({favorites: []})

// Calling setState() automatically calls:
window.openai.setWidgetState(newState)

// ChatGPT stores state in conversation context
// State restored when widget remounts
```

---

### "What's the MCP protocol flow?"
→ **WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md** → MCP Request-Response Flow  
→ **WEB_RESOURCES_TECHNICAL_GUIDE.md** → Phase 4: Tool Execution

**Quick Answer:**
1. ChatGPT calls tool via `POST /mcp/messages`
2. Server handler `_call_tool_request()` executes
3. Fetches data, builds `structuredContent`
4. Embeds widget resource in `_meta`
5. Returns `CallToolResult` with both data and UI
6. ChatGPT renders

---

### "How to add a new widget?"
→ **QUICK_REFERENCE_WEB_RESOURCES.md** → 🚀 Adding a New Widget  
→ **WEB_RESOURCES_TECHNICAL_GUIDE.md** → Example 1: Adding a New Widget

**Quick Answer:**
1. Create `web/src/NewWidget.tsx`
2. Build: `npm run build`
3. Load bundle in `server.py`
4. Add to `widgets` list
5. Add tool handler

---

### "How to debug widget not showing?"
→ **QUICK_REFERENCE_WEB_RESOURCES.md** → 🐛 Debugging Checklist  
→ **WEB_RESOURCES_TECHNICAL_GUIDE.md** → Debugging & Troubleshooting → Common Issues

**Quick Answer:**
- Bundle built? Check `web/dist/`
- Server loaded? Check startup logs
- MIME type? Should be `text/html+skybridge`
- HTML structure? Need `<div id="...">` + `<script>`

---

## 📖 Code Examples by Use Case

### Use Case 1: Reading Server Data
**Location:** QUICK_REFERENCE_WEB_RESOURCES.md → Code Snippets → React: Access Data

```typescript
const PlayerListApp = () => {
  const toolOutput = useToolOutput<{players: PlayerData[]}>();
  const players = toolOutput?.players || [];
  return <div>{players.map(p => <Card player={p} />)}</div>;
};
```

---

### Use Case 2: Adapting to Theme
**Location:** QUICK_REFERENCE_WEB_RESOURCES.md → Code Snippets → React: Access Data

```typescript
const theme = useTheme();
const isDark = theme === "dark";
const colors = {
  background: isDark ? "#1a1a1a" : "#ffffff",
  text: isDark ? "#ffffff" : "#000000"
};
```

---

### Use Case 3: Persisting State
**Location:** WEB_RESOURCES_TECHNICAL_GUIDE.md → React Component Integration → Widget State Hook

```typescript
const [widgetState, setWidgetState] = useWidgetState({favorites: []});

const addFavorite = (id) => {
  setWidgetState({
    ...widgetState,
    favorites: [...widgetState.favorites, id]
  });
};
```

---

### Use Case 4: Returning Data from Server
**Location:** WEB_RESOURCES_TECHNICAL_GUIDE.md → Phase 4: Tool Execution

```python
async def _call_tool_request(req):
    # Fetch data
    data = await fetch_fpl_data()
    
    # Return with widget
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(text="Done!")],
            structuredContent={"players": data},
            _meta={"openai.com/widget": widget_resource}
        )
    )
```

---

## 🛠️ Development Checklists

### Adding a New Widget
- [ ] Create React component in `web/src/`
- [ ] Build with `npm run build`
- [ ] Load bundle in `server.py` at startup
- [ ] Create `FPLWidget` configuration
- [ ] Add to `widgets` list
- [ ] Add tool handler in `_call_tool_request()`
- [ ] Add input schema (Pydantic)
- [ ] Test with ChatGPT

**Detailed Guide:** QUICK_REFERENCE_WEB_RESOURCES.md → 🚀 Adding a New Widget

---

### Debugging Widget Issues
- [ ] Check bundle built: `ls web/dist/`
- [ ] Check server loaded: startup logs
- [ ] Check MIME type: `text/html+skybridge`
- [ ] Check HTML structure: `<div>` + `<script>`
- [ ] Check data: `console.log(toolOutput)`
- [ ] Check theme: using `useTheme()`
- [ ] Check state: using `useWidgetState`

**Detailed Guide:** WEB_RESOURCES_TECHNICAL_GUIDE.md → Debugging & Troubleshooting

---

### Performance Optimization
- [ ] Minify bundles: `esbuild --minify`
- [ ] Cache API responses: 5 min TTL
- [ ] Use `useMemo` for expensive computations
- [ ] Lazy load components if >100KB
- [ ] Monitor bundle sizes
- [ ] Profile with React DevTools

**Detailed Guide:** WEB_RESOURCES_TECHNICAL_GUIDE.md → Performance Optimization

---

## 📊 File Reference

### Server Files
| File | Purpose | Documentation |
|------|---------|---------------|
| `server.py` | Main MCP server | All guides |
| `fpl_utils.py` | FPL API client | Technical Guide |
| `mcp_server/ux_components.py` | Formatting utils | Technical Guide |

### React Files
| File | Purpose | Documentation |
|------|---------|---------------|
| `web/src/PlayerListComponent.tsx` | Player list widget | All guides |
| `web/src/PlayerDetailComponent.tsx` | Player detail widget | Technical Guide |
| `web/src/PlayerComparisonComponent.tsx` | Comparison widget | Technical Guide |
| `web/src/hooks.ts` | OpenAI hooks | Technical Guide → React Hooks |
| `web/src/types.ts` | Type definitions | Technical Guide → OpenAI API |

### Build Files
| File | Purpose | Documentation |
|------|---------|---------------|
| `web/package.json` | NPM dependencies | Quick Reference |
| `web/tsconfig.json` | TypeScript config | Technical Guide |
| `web/dist/*.js` | Compiled bundles | Technical Guide → Phase 1 |

---

## 🔗 External Resources

### MCP Protocol
- **MCP Specification:** https://modelcontextprotocol.io/
- **FastMCP Framework:** https://github.com/jlowin/fastmcp

### OpenAI Apps SDK
- **Apps SDK Docs:** https://developers.openai.com/apps-sdk
- **Design Guidelines:** https://developers.openai.com/apps-sdk/concepts/design-guidelines
- **Custom UX Guide:** https://developers.openai.com/apps-sdk/build/custom-ux

### React
- **React 18 Docs:** https://react.dev/
- **useSyncExternalStore:** https://react.dev/reference/react/useSyncExternalStore
- **React DevTools:** https://react.dev/learn/react-developer-tools

### Build Tools
- **esbuild:** https://esbuild.github.io/
- **TypeScript:** https://www.typescriptlang.org/

---

## 💡 Tips for Reading

### If You're Visual
Start with **WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md** - it has comprehensive diagrams showing every aspect of the system.

### If You're Hands-On
Start with **QUICK_REFERENCE_WEB_RESOURCES.md** → "🚀 Adding a New Widget" and build something immediately.

### If You're Systematic
Read **WEB_RESOURCES_TECHNICAL_GUIDE.md** from start to finish - it explains everything in order.

### If You're in a Hurry
Check **QUICK_REFERENCE_WEB_RESOURCES.md** → look up what you need in the tables and checklists.

---

## 🎯 Document Goals

These documents aim to:
1. **Eliminate confusion** about how React bundles reach ChatGPT
2. **Provide copy-paste examples** for common tasks
3. **Enable quick debugging** with checklists
4. **Show the complete picture** with diagrams
5. **Support all learning styles** (visual, textual, hands-on)

---

## 📝 Document Maintenance

### Updating Documentation
When you change the code, update:
- Code snippets in Technical Guide
- Diagrams in Architecture Diagram
- Tables in Quick Reference

### Adding New Features
Document in this order:
1. Add to Architecture Diagram (new flow chart)
2. Add to Technical Guide (detailed explanation)
3. Add to Quick Reference (lookup table entry)

---

## 🙏 Feedback

If you find:
- **Missing information:** Add to Technical Guide
- **Confusing explanation:** Clarify in Quick Reference
- **Missing diagram:** Add to Architecture Diagram
- **Common question:** Add to "Key Questions Answered"

---

**Documentation Version:** 1.0  
**Last Updated:** October 11, 2025  
**Project:** FPL MCP Server (fpl-deepagent)  

---

## 🚀 Quick Start

**New to project?** Read this order:
1. PROJECT_OVERVIEW.md (5 min)
2. WEB_RESOURCES_ARCHITECTURE_DIAGRAM.md (10 min)
3. QUICK_REFERENCE_WEB_RESOURCES.md (15 min)

**Need to build?** Go to:
→ QUICK_REFERENCE_WEB_RESOURCES.md → "🚀 Adding a New Widget"

**Need to debug?** Go to:
→ QUICK_REFERENCE_WEB_RESOURCES.md → "🐛 Debugging Checklist"

**Need complete understanding?** Read:
→ WEB_RESOURCES_TECHNICAL_GUIDE.md (all sections)

