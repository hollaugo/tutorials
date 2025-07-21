#!/usr/bin/env python3
"""
Setup script for Notion MCP Agent environment variables
"""
import os
from pathlib import Path

def create_env_file():
    """Create a .env file with required environment variables"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("✅ .env file already exists")
        return
    
    env_content = """# Notion MCP Agent Environment Variables

# Notion API Token (required)
# Get this from: https://www.notion.so/my-integrations
NOTION_TOKEN=your_notion_integration_token_here

# OpenAI API Key (required)
# Get this from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Server Configuration (optional)
PORT=8006
"""
    
    with open(env_path, "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("📝 Please edit .env file and add your actual API keys")

def check_environment():
    """Check if required environment variables are set"""
    print("\n🔍 Checking environment variables...")
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["NOTION_TOKEN", "OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith("your_"):
            missing_vars.append(var)
            print(f"❌ {var}: Not set or using placeholder")
        else:
            print(f"✅ {var}: Set")
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please edit the .env file and add your actual API keys")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True

def main():
    print("🚀 Notion MCP Agent Setup")
    print("=" * 40)
    
    # Create .env file if it doesn't exist
    create_env_file()
    
    # Check environment
    env_ok = check_environment()
    
    if env_ok:
        print("\n🎉 Setup complete! You can now run:")
        print("  python server.py")
        print("  python langgraph-agent-client.py")
    else:
        print("\n📋 Next steps:")
        print("1. Edit .env file with your actual API keys")
        print("2. Run this script again to verify setup")
        print("3. Start the server: python server.py")

if __name__ == "__main__":
    main() 