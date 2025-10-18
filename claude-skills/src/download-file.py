import anthropic
from dotenv import load_dotenv
import os
import sys

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

if len(sys.argv) < 2:
    print("❌ Error: Please provide a file_id")
    print("\nUsage:")
    print("   uv run src/download-file.py <file_id>")
    print("\n💡 Tip: Use 'uv run src/list-files.py' to see available files")
    sys.exit(1)

file_id = sys.argv[1]

print(f"📥 Downloading file: {file_id}\n")
print("=" * 60)

try:
    # Get file metadata
    file_metadata = client.beta.files.retrieve_metadata(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )
    
    print(f"📄 File: {file_metadata.filename}")
    print(f"   Size: {file_metadata.size_bytes:,} bytes")
    print(f"   Created: {file_metadata.created_at}")
    print()
    
    # Download file content
    print("⬇️  Downloading...")
    file_content = client.beta.files.download(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )
    
    # Save to disk
    file_content.write_to_file(file_metadata.filename)
    
    print(f"✅ Saved to: {file_metadata.filename}")
    print("=" * 60)

except anthropic.NotFoundError:
    print(f"❌ Error: File '{file_id}' not found")
    print("\n💡 Tip: Use 'uv run src/list-files.py' to see available files")
except anthropic.BadRequestError as e:
    print(f"❌ Error: {e}")
    if "credit balance" in str(e).lower():
        print("\n💡 Add credits at: https://console.anthropic.com/settings/plans")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

