import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=300.0
)

def extract_file_ids(response):
    """Extract file IDs from the response"""
    file_ids = []
    for item in response.content:
        if item.type == 'bash_code_execution_tool_result':
            content_item = item.content
            if content_item.type == 'bash_code_execution_result':
                for file in content_item.content:
                    if hasattr(file, 'file_id'):
                        file_ids.append(file.file_id)
    return file_ids

def download_files(client, file_ids):
    """Download files using the Files API"""
    downloaded = []
    for file_id in file_ids:
        # Get file metadata
        file_metadata = client.beta.files.retrieve_metadata(
            file_id=file_id,
            betas=["files-api-2025-04-14"]
        )
        
        print(f"   📄 Downloading: {file_metadata.filename}")
        print(f"      Size: {file_metadata.size_bytes:,} bytes")
        
        # Download file content
        file_content = client.beta.files.download(
            file_id=file_id,
            betas=["files-api-2025-04-14"]
        )
        
        # Save to disk
        file_content.write_to_file(file_metadata.filename)
        print(f"      ✅ Saved to: {file_metadata.filename}\n")
        downloaded.append(file_metadata.filename)
    
    return downloaded

print("🎯 Multi-Skill Demo: Using Excel and PowerPoint together\n")
print("=" * 70)

try:
    # Use multiple skills together
    with client.beta.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        betas=["code-execution-2025-08-25", "skills-2025-10-02", "files-api-2025-04-14"],
        container={
            "skills": [
                {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
                {"type": "anthropic", "skill_id": "pptx", "version": "latest"}
            ]
        },
        messages=[{
            "role": "user",
            "content": """Create a quarterly sales report:
            1. Excel file with sales data for Q1-Q4 (Product A, B, C with realistic numbers)
            2. PowerPoint presentation summarizing the data with charts"""
        }],
        tools=[{
            "type": "code_execution_20250825",
            "name": "code_execution"
        }]
    ) as stream:
        print("🤖 Claude is working on your request...\n")
        print("Response:")
        print("-" * 70)
        
        for text in stream.text_stream:
            print(text, end="", flush=True)
        
        print("\n" + "-" * 70)
        
        # Get final message
        message = stream.get_final_message()
    
    # Download generated files
    print("\n📁 Downloading generated files...")
    file_ids = extract_file_ids(message)
    
    if file_ids:
        print(f"   Found {len(file_ids)} file(s)\n")
        downloaded_files = download_files(client, file_ids)
        
        print("\n" + "=" * 70)
        print("✅ Successfully downloaded:")
        for filename in downloaded_files:
            print(f"   • {filename}")
        print("=" * 70)
    else:
        print("   No files were generated")

except anthropic.BadRequestError as e:
    print(f"\n❌ Error: {e}")
    if "credit balance" in str(e).lower():
        print("\n💡 Add credits at: https://console.anthropic.com/settings/plans")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")

