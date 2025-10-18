import anthropic
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print("📂 Listing all files in your workspace...\n")
print("=" * 80)

try:
    # List all files
    files_response = client.beta.files.list(betas=["files-api-2025-04-14"])
    
    if files_response.data:
        print(f"Found {len(files_response.data)} file(s):\n")
        
        for i, file in enumerate(files_response.data, 1):
            # Format the timestamp
            created = datetime.fromisoformat(file.created_at.replace('Z', '+00:00'))
            
            print(f"{i}. {file.filename}")
            print(f"   ID: {file.id}")
            print(f"   Size: {file.size_bytes:,} bytes")
            print(f"   Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        print("=" * 80)
        print("\n💡 To download a file, use:")
        print("   python src/download-file.py <file_id>")
        
    else:
        print("No files found in your workspace.")
        print("\n💡 Files are created when using Skills that generate documents")
        print("   (e.g., pptx, xlsx, docx, pdf)")
    
    print("\n" + "=" * 80)

except anthropic.BadRequestError as e:
    print(f"❌ Error: {e}")
    if "credit balance" in str(e).lower():
        print("\n💡 Add credits at: https://console.anthropic.com/settings/plans")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

