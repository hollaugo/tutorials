# Claude Skills API - Utility Scripts

A collection of Python utilities for working with the Claude Skills API.

## 📋 Table of Contents

- [Setup](#setup)
- [Skills Management](#skills-management)
- [Using Skills](#using-skills)
- [File Management](#file-management)
- [Examples](#examples)

---

## 🚀 Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up your API key:**
   Create a `.env` file in the project root:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

3. **Get your API key:**
   Visit [console.anthropic.com](https://console.anthropic.com/settings/keys)

---

## 🎯 Skills Management

### List All Skills
Lists all available skills (both Anthropic and custom).

```bash
uv run src/list-skills.py
```

**Features:**
- Pagination support for large skill lists
- Shows skill ID, version, source, and last update
- Works with both Anthropic-provided and custom skills

### Create a Custom Skill
Upload a custom skill from a directory or zip file.

```bash
uv run src/create-skill.py
```

**Requirements:**
- Skill folder name must match the `name` field in `SKILL.md`
- Maximum upload size: 8MB
- Must include a `SKILL.md` file with YAML frontmatter

**Example SKILL.md:**
```markdown
---
name: my-custom-skill
description: A custom skill for specific tasks
---

# My Custom Skill
...
```

### Get Skill Details
Retrieve details about a specific skill.

```bash
uv run src/get-skill.py
```

---

## 💻 Using Skills

### Use a Single Skill
Create documents using Anthropic's built-in skills.

```bash
uv run src/use-skill.py
```

**Features:**
- Streaming support for real-time progress
- Automatic file detection and download
- 5-minute timeout for long operations
- Error handling with helpful tips

**Available Anthropic Skills:**
- `pptx` - PowerPoint presentations
- `xlsx` - Excel spreadsheets
- `docx` - Word documents
- `pdf` - PDF files

### Multi-Skill Demo
Use multiple skills together for complex workflows.

```bash
uv run src/multi-skill-demo.py
```

**Example use case:**
Create a quarterly sales report with both Excel data and PowerPoint presentation.

**Features:**
- Combines multiple skills (e.g., Excel + PowerPoint)
- Automatic file download for all generated files
- Progress tracking with streaming

---

## 📁 File Management

### List All Files
View all files in your workspace.

```bash
uv run src/list-files.py
```

**Output:**
- Filename
- File ID
- Size in bytes
- Creation timestamp

### Download a Specific File
Download a file by its ID.

```bash
uv run src/download-file.py <file_id>
```

**Example:**
```bash
uv run src/download-file.py file_01AbCdEfGhIjKlMnOpQrStUv
```

### Delete a File
Remove a file from your workspace.

```bash
uv run src/delete-file.py <file_id>
```

**Features:**
- Shows file details before deletion
- Requires confirmation (yes/no prompt)
- Safe deletion with error handling

---

## 📚 Examples

### Example 1: Create a PowerPoint Presentation

```python
import anthropic

client = anthropic.Anthropic(api_key="your-key")

with client.beta.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02", "files-api-2025-04-14"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "pptx", "version": "latest"}
        ]
    },
    messages=[{
        "role": "user",
        "content": "Create a presentation about renewable energy"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    
    message = stream.get_final_message()
    
# Download generated files
file_ids = extract_file_ids(message)
for file_id in file_ids:
    file_content = client.beta.files.download(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )
    file_content.write_to_file("presentation.pptx")
```

### Example 2: Create an Excel Spreadsheet

```python
with client.beta.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02", "files-api-2025-04-14"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    messages=[{
        "role": "user",
        "content": "Create a budget spreadsheet with income and expenses"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
) as stream:
    message = stream.get_final_message()
```

### Example 3: Using Multiple Skills

```python
container={
    "skills": [
        {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
        {"type": "anthropic", "skill_id": "pptx", "version": "latest"}
    ]
}
```

### Example 4: Using a Custom Skill

```python
# First, create the skill
skill = client.beta.skills.create(
    display_title="My Custom Skill",
    files=files_from_dir("path/to/skill"),
    betas=["skills-2025-10-02"]
)

# Then use it
container={
    "skills": [
        {"type": "custom", "skill_id": skill.id, "version": "latest"}
    ]
}
```

---

## 🔧 Best Practices

### 1. **Version Management**

**Production (stable):**
```python
"version": "1759178010641129"  # Pin to specific version
```

**Development (latest):**
```python
"version": "latest"  # Always use newest version
```

### 2. **Timeout Handling**

For long-running operations (document generation), increase timeout:

```python
client = anthropic.Anthropic(
    api_key=api_key,
    timeout=300.0  # 5 minutes
)
```

### 3. **Use Streaming for Better UX**

Always use streaming for Skills operations:

```python
with client.beta.messages.stream(...) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### 4. **Error Handling**

```python
try:
    response = client.beta.messages.create(...)
except anthropic.BadRequestError as e:
    if "credit balance" in str(e).lower():
        print("Add credits at console.anthropic.com")
    elif "skill" in str(e).lower():
        print("Check skill_id and version")
except anthropic.APITimeoutError:
    print("Operation timed out - increase timeout")
```

### 5. **File Management**

Always clean up files you no longer need:

```python
# List files periodically
files = client.beta.files.list(betas=["files-api-2025-04-14"])

# Delete old files
for file in files.data:
    client.beta.files.delete(file_id=file.id, betas=["files-api-2025-04-14"])
```

---

## 🚨 Limits and Constraints

### Request Limits
- **Max 8 skills** per request
- **Max 8MB** skill upload size
- **YAML frontmatter**: `name` ≤ 64 chars, `description` ≤ 1024 chars

### Environment Constraints
- ❌ No network access in code execution
- ❌ No runtime package installation
- ✅ Isolated environment per request

---

## 📖 Additional Resources

- [Claude Skills API Documentation](https://docs.claude.com/en/api/skills-guide)
- [Skills API Reference](https://docs.claude.com/en/api/skills/create-skill)
- [Code Execution Tool](https://docs.claude.com/en/docs/build-with-claude/tool-use)
- [Anthropic Console](https://console.anthropic.com/)

---

## 🐛 Troubleshooting

### "Credit balance is too low"
Add credits at [console.anthropic.com/settings/plans](https://console.anthropic.com/settings/plans)

### "Folder name must match skill name"
The folder name must match the `name` field in your `SKILL.md` file.

### "Operation timed out"
Increase the timeout:
```python
client = anthropic.Anthropic(timeout=600.0)  # 10 minutes
```

### "Expected UploadFile"
Use `files_from_dir()` helper or proper file handles:
```python
from anthropic.lib import files_from_dir
files=files_from_dir("path/to/skill")
```

---

## 📝 License

MIT License - See LICENSE file for details

