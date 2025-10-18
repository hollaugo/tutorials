import anthropic
from dotenv import load_dotenv
import os
import sys

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

if len(sys.argv) < 2:
    print("❌ Error: Please provide a file_id")
    print("\nUsage:")
    print("   uv run src/delete-file.py <file_id>")
    print("\n💡 Tip: Use 'uv run src/list-files.py' to see available files")
    sys.exit(1)

file_id = sys.argv[1]

print(f"🗑️  Deleting file: {file_id}\n")
print("=" * 60)

try:
    # Get file metadata first to show what we're deleting
    file_metadata = client.beta.files.retrieve_metadata(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )
    
    print(f"📄 File: {file_metadata.filename}")
    print(f"   Size: {file_metadata.size_bytes:,} bytes")
    print(f"   Created: {file_metadata.created_at}")
    print()
    
    # Confirm deletion
    confirm = input("⚠️  Are you sure you want to delete this file? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        # Delete the file
        client.beta.files.delete(
            file_id=file_id,
            betas=["files-api-2025-04-14"]
        )
        
        print(f"\n✅ File '{file_metadata.filename}' deleted successfully")
    else:
        print("\n❌ Deletion cancelled")
    
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

