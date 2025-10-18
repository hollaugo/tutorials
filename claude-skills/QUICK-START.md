# Claude Skills API - Quick Start Guide

## ⚡ Quick Commands

### Skills Management
```bash
# List all available skills
uv run src/list-skills.py

# Create a custom skill
uv run src/create-skill.py

# Get skill details
uv run src/get-skill.py
```

### Using Skills
```bash
# Use a single skill (PowerPoint)
uv run src/use-skill.py

# Use multiple skills together
uv run src/multi-skill-demo.py
```

### File Management
```bash
# List all files
uv run src/list-files.py

# Download a specific file
uv run src/download-file.py <file_id>

# Delete a file
uv run src/delete-file.py <file_id>
```

---

## 📦 Available Scripts

| Script | Purpose | Key Features |
|--------|---------|--------------|
| `list-skills.py` | List all skills | Pagination, shows Anthropic + custom skills |
| `create-skill.py` | Upload custom skill | Uses `files_from_dir` helper |
| `get-skill.py` | Get skill details | Shows skill metadata |
| `use-skill.py` | Use a skill | Streaming, auto-download, error handling |
| `multi-skill-demo.py` | Use multiple skills | Excel + PowerPoint example |
| `list-files.py` | List all files | Shows file metadata |
| `download-file.py` | Download file by ID | Saves to current directory |
| `delete-file.py` | Delete file by ID | Confirmation prompt |

---

## 🎯 Common Tasks

### Create a PowerPoint Presentation
```python
container={
    "skills": [
        {"type": "anthropic", "skill_id": "pptx", "version": "latest"}
    ]
}
messages=[{"role": "user", "content": "Create a presentation about AI"}]
```

### Create an Excel Spreadsheet
```python
container={
    "skills": [
        {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
    ]
}
messages=[{"role": "user", "content": "Create a budget spreadsheet"}]
```

### Create a Word Document
```python
container={
    "skills": [
        {"type": "anthropic", "skill_id": "docx", "version": "latest"}
    ]
}
messages=[{"role": "user", "content": "Create a project proposal"}]
```

### Create a PDF
```python
container={
    "skills": [
        {"type": "anthropic", "skill_id": "pdf", "version": "latest"}
    ]
}
messages=[{"role": "user", "content": "Create a report as PDF"}]
```

---

## 🔑 Required Beta Headers

All Skills operations require these beta headers:

```python
betas=[
    "code-execution-2025-08-25",  # Code execution (required)
    "skills-2025-10-02",          # Skills API
    "files-api-2025-04-14"        # File operations
]
```

---

## 📝 Skill Structure

Custom skills must have this structure:

```
my-skill/
├── SKILL.md          # Required: Metadata + instructions
├── scripts/          # Optional: Python scripts
│   └── helper.py
└── examples/         # Optional: Examples
    └── example.md
```

**SKILL.md format:**
```markdown
---
name: my-skill
description: A description of what this skill does
---

# My Skill

Instructions for Claude on how to use this skill...
```

---

## 🚨 Quick Troubleshooting

| Error | Solution |
|-------|----------|
| "Credit balance too low" | Add credits at console.anthropic.com |
| "Folder name must match skill name" | Rename folder to match `name` in SKILL.md |
| "Operation timed out" | Increase timeout: `Anthropic(timeout=300.0)` |
| "Expected UploadFile" | Use `files_from_dir()` helper |
| No files downloaded | Check response with `extract_file_ids()` |

---

## 💡 Pro Tips

1. **Use streaming for long operations**
   ```python
   with client.beta.messages.stream(...) as stream:
       for text in stream.text_stream:
           print(text, end="", flush=True)
   ```

2. **Pin versions in production**
   ```python
   "version": "1759178010641129"  # Not "latest"
   ```

3. **Increase timeout for document generation**
   ```python
   client = anthropic.Anthropic(timeout=300.0)  # 5 minutes
   ```

4. **Handle errors gracefully**
   ```python
   try:
       response = client.beta.messages.create(...)
   except anthropic.BadRequestError as e:
       print(f"Error: {e}")
   ```

5. **Clean up old files**
   ```bash
   uv run src/list-files.py  # Check files
   uv run src/delete-file.py <file_id>  # Delete old ones
   ```

---

## 📚 Learn More

- **Full README**: [src/README.md](src/README.md)
- **API Docs**: https://docs.claude.com/en/api/skills-guide
- **Console**: https://console.anthropic.com/
- **Support**: https://support.anthropic.com/

---

## 🎉 You're Ready!

Once you have credits, run:
```bash
uv run src/use-skill.py
```

This will create a PowerPoint presentation and automatically download it! 🚀

