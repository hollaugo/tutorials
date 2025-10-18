# OpenAI Apps SDK Skill Package

**Version:** 1.0.0  
**Created:** October 2024  
**For:** Claude AI Assistant (Anthropic)

## 📦 What's Inside

This package contains a comprehensive skill that teaches Claude how to build OpenAI Apps SDK applications - interactive apps that run inside ChatGPT with rich UI widgets.

### Package Contents

```
openai-apps-sdk-skill-package/
├── README.md                    # This file
├── SKILL.md                     # Main skill file (install this!)
├── LICENSE                      # MIT License
├── scripts/                     # Utility scripts
│   ├── README.md                # Scripts documentation
│   ├── QUICK-REFERENCE.md       # Quick reference card
│   ├── validate_mcp_response.py # Validate responses
│   ├── test_mcp_server.py       # Test MCP servers
│   ├── scaffold_project.py      # Create new projects
│   ├── check_cors.py            # Verify CORS config
│   └── test-data/               # Example test files
│       ├── valid_tool_response.json
│       ├── invalid_tool_response.json
│       └── valid_resource_response.json
├── docs/                        # Documentation
│   ├── OpenAI-Apps-SDK-README.md
│   └── COMPLETE-PACKAGE-SUMMARY.md
└── examples/                    # Example apps
    └── Example-Pizza-Finder-App.md
```

---

## 🚀 Quick Start

### Installation

1. **Extract this package** to your desired location
2. **Copy the skill file** to Claude's skills directory:
   ```bash
   # If using MCP with Claude Desktop/CLI
   mkdir -p ~/.claude/skills/openai-apps-sdk
   cp SKILL.md ~/.claude/skills/openai-apps-sdk/
   cp -r scripts ~/.claude/skills/openai-apps-sdk/
   ```

3. **Install script dependencies** (optional, for scripts):
   ```bash
   pip install aiohttp
   ```

### Using the Skill

Once installed, simply ask Claude:

```
"Create an OpenAI app that finds coffee shops near me with a map"
```

Claude will automatically use this skill to generate:
- ✅ Complete MCP server (Python or TypeScript)
- ✅ React widget components
- ✅ Build configuration
- ✅ Testing instructions
- ✅ Deployment guides

---

## 🛠️ What This Skill Does

The OpenAI Apps SDK Skill enables Claude to build apps for ChatGPT that combine:
- **Conversational AI** - Natural language interaction
- **Rich Widgets** - Interactive UI components (maps, charts, galleries, etc.)
- **MCP Protocol** - Standardized server-to-ChatGPT communication

### Key Features

- **Full-stack development** - Backend (MCP server) + Frontend (React widgets)
- **Both Python & TypeScript** - Choose your preferred language
- **Best practices built-in** - Security, CORS, validation, testing
- **Production-ready** - Complete deployment guides
- **Comprehensive** - Covers tools, resources, metadata, state management

---

## 📚 Documentation

### For Users

- **`docs/OpenAI-Apps-SDK-README.md`** - Overview and getting started guide
- **`docs/COMPLETE-PACKAGE-SUMMARY.md`** - Complete feature list and workflows
- **`examples/Example-Pizza-Finder-App.md`** - Full working example

### For Developers

- **`SKILL.md`** - Complete skill documentation (this is what Claude reads)
- **`scripts/README.md`** - Detailed script documentation
- **`scripts/QUICK-REFERENCE.md`** - Command cheat sheet

---

## 🔧 Utility Scripts

Four powerful scripts included for validation and testing:

### 1. Response Validator
```bash
python scripts/validate_mcp_response.py response.json
```
Validates that MCP responses conform to OpenAI Apps SDK requirements.

### 2. Server Tester
```bash
python scripts/test_mcp_server.py http://localhost:8000
```
Test your MCP server without needing ChatGPT.

### 3. Project Scaffolder
```bash
python scripts/scaffold_project.py my-app
```
Create a new project with complete structure instantly.

### 4. CORS Checker
```bash
python scripts/check_cors.py http://localhost:8000
```
Verify CORS configuration for ChatGPT compatibility.

**See `scripts/README.md` for detailed usage.**

---

## 💡 Example Use Cases

This skill helps build:

- 🗺️ **Location apps** - Restaurant finders, store locators, real estate
- 📊 **Data visualization** - Charts, graphs, analytics dashboards
- 🎵 **Media apps** - Music/video players, podcast browsers
- ✅ **Productivity** - Task managers, calendars, note apps
- 🛒 **E-commerce** - Product catalogs, shopping carts
- 📚 **Educational** - Quiz apps, flashcards, courses

---

## 🎓 Learning Path

### Beginner
1. Install the skill
2. Ask Claude to build a simple app
3. Run the generated code locally
4. Test with the included scripts
5. Deploy with ngrok

### Intermediate  
1. Use the scaffolder for custom projects
2. Modify widgets and server logic
3. Add real API integrations
4. Implement authentication
5. Deploy to production

### Advanced
1. Build multi-widget applications
2. Create reusable components
3. Implement complex state management
4. Optimize for scale
5. Contribute improvements

---

## 📋 Requirements

### For Using the Skill
- Claude AI Assistant (Claude Desktop, API, or compatible client)
- Access to Claude's skills system

### For Generated Apps
- **Node.js 18+** (for frontend widgets)
- **Python 3.10+** OR **Node.js 18+** (for MCP server)
- **npm** or **pnpm** (package manager)

### For Scripts (Optional)
- **Python 3.8+**
- **aiohttp** (`pip install aiohttp`)

---

## 🔒 Security Notes

The skill teaches best practices for secure app development:

- ✅ Proper CORS configuration (restricted to `https://chatgpt.com`)
- ✅ Input validation with schemas
- ✅ OAuth 2.1 authentication patterns
- ✅ No sensitive data in widget state
- ✅ CSP (Content Security Policy) configuration
- ✅ Rate limiting recommendations

---

## 🤝 Support & Resources

### Official Documentation
- **OpenAI Apps SDK**: https://developers.openai.com/apps-sdk/
- **MCP Specification**: https://spec.modelcontextprotocol.io/
- **Examples Repository**: https://github.com/openai/openai-apps-sdk-examples

### SDKs & Libraries
- **Python MCP SDK**: https://github.com/modelcontextprotocol/python-sdk
- **TypeScript MCP SDK**: https://github.com/modelcontextprotocol/typescript-sdk
- **FastMCP**: https://github.com/jlowin/fastmcp

---

## 📄 License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 🎯 Quick Examples

### Create Your First App
```
User: "Claude, create an OpenAI app that tracks my daily habits"

Claude: [Uses this skill to generate complete app with:]
  - MCP server with habit tracking tools
  - React widget with calendar visualization
  - Build configuration
  - Testing workflow
  - Deployment instructions
```

### Test a Server
```bash
cd my-app
npm start

# In another terminal
cd ../openai-apps-sdk-skill-package
python scripts/test_mcp_server.py http://localhost:8000
```

### Validate Responses
```bash
# Save tool response to file, then:
python scripts/validate_mcp_response.py tool_response.json
```

---

## 🌟 What Makes This Skill Special

1. **Comprehensive** - Covers everything from setup to deployment
2. **Practical** - Includes working examples and test data
3. **Production-Ready** - Best practices and security built-in
4. **Well-Tested** - Validation and testing tools included
5. **Flexible** - Supports both Python and TypeScript
6. **Documented** - Extensive guides and references
7. **Maintained** - Based on official OpenAI documentation

---

## 🚧 Troubleshooting

### Skill Not Loading
1. Check skill file location
2. Ensure SKILL.md is in proper directory
3. Restart Claude if necessary

### Scripts Not Working
```bash
# Check Python version
python --version  # Need 3.8+

# Install dependencies
pip install aiohttp

# Make executable (Unix/Mac)
chmod +x scripts/*.py
```

### Generated Apps Not Working
1. Run validation scripts on responses
2. Check CORS configuration
3. Verify MIME types
4. See troubleshooting section in SKILL.md

---

## 📞 Getting Help

1. **Read the docs**: Start with `docs/OpenAI-Apps-SDK-README.md`
2. **Check examples**: See `examples/Example-Pizza-Finder-App.md`
3. **Use scripts**: Test and validate your implementation
4. **Review skill**: Look at `SKILL.md` for detailed patterns
5. **Check official docs**: OpenAI Apps SDK documentation

---

## 🎉 Ready to Build!

Everything you need is in this package. Just:

1. ✅ Install the skill
2. ✅ Ask Claude to build an app
3. ✅ Test with included scripts
4. ✅ Deploy and enjoy!

**Let's build something amazing for ChatGPT! 🚀**

---

**Package Version**: 1.0.0  
**Last Updated**: October 2024  
**Skill Author**: Created via analysis of OpenAI Apps SDK documentation and examples
