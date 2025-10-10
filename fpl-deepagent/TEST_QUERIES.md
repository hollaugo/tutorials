# 🧪 Test Queries for FPL MCP Server

## ✅ Correct Query Formats

### **Show Top Forwards by Form**

**Correct way:**
```json
{
  "position": "FWD",
  "limit": 10
}
```

Or use the generic terms:
```json
{
  "query": "top form",
  "position": "forward",
  "limit": 10
}
```

**Now works with:**
- `"forward"`, `"forwards"`, `"FWD"`, `"striker"`, `"strikers"`
- Auto-converts to FWD internally
- Sorts by form when query contains "form"

---

### **Search for Specific Player**

```json
{
  "query": "Haaland"
}
```

```json
{
  "query": "Salah",
  "position": "MID"
}
```

---

### **Filter by Position**

```json
{
  "position": "midfielder",
  "limit": 15
}
```

Accepts:
- **Goalkeepers**: `"goalkeeper"`, `"GK"`, `"keeper"`
- **Defenders**: `"defender"`, `"DEF"`, `"defenders"`, `"defence"`
- **Midfielders**: `"midfielder"`, `"MID"`, `"midfielders"`, `"midfield"`
- **Forwards**: `"forward"`, `"FWD"`, `"forwards"`, `"striker"`, `"strikers"`

---

### **Filter by Price**

```json
{
  "position": "FWD",
  "max_price": 10.0,
  "limit": 10
}
```

---

### **Combine Filters**

```json
{
  "position": "midfielder",
  "max_price": 8.0,
  "limit": 15
}
```

---

## 🎯 Example Queries

### Best Forwards
```json
{
  "query": "top",
  "position": "forward",
  "limit": 10
}
```

### Cheap Defenders
```json
{
  "position": "DEF",
  "max_price": 5.0,
  "limit": 10
}
```

### Search Salah
```json
{
  "query": "Salah"
}
```

### Top Form Players (Any Position)
```json
{
  "query": "top form",
  "limit": 15
}
```

---

## 🚀 Test Now

```bash
cd /Users/uosuji/prompt-circle-phoenix/tutorials/fpl-deepagent

# Start server
uv run python server_final.py

# In browser or new terminal
npx @modelcontextprotocol/inspector uv run python server_final.py --stdio
```

**Try these in Inspector:**

1. `show_players` with `{"position": "FWD", "limit": 10}`
2. `show_players` with `{"query": "Haaland"}`
3. `show_players` with `{"query": "top form", "position": "forward", "limit": 10}`

All should work now! ✅

