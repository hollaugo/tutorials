import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=300.0  # 5 minute timeout for long-running operations
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

print("🚀 Starting Skills request (with streaming for progress)...\n")

try:
    # Use streaming for long-running operations
    with client.beta.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        betas=["code-execution-2025-08-25", "skills-2025-10-02", "files-api-2025-04-14"],
        container={
            "skills": [
                {
                    "type": "anthropic",
                    "skill_id": "pptx",
                    "version": "latest"
                }
            ]
        },
        messages=[{
            "role": "user",
            "content": "Create a one slide presentation about mcp servers"
        }],
        tools=[{
            "type": "code_execution_20250825",
            "name": "code_execution"
        }]
    ) as stream:
        print("🤖 Response:")
        print("=" * 60)
        
        for text in stream.text_stream:
            print(text, end="", flush=True)
        
        print("\n" + "=" * 60)
        
        # Get final message
        message = stream.get_final_message()
    
    # Extract and download generated files
    print("\n📁 Checking for generated files...")
    file_ids = extract_file_ids(message)
    
    if file_ids:
        print(f"   Found {len(file_ids)} file(s) to download\n")
        
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
    else:
        print("   No files generated")
    
    print("✅ Request completed!")

except anthropic.APITimeoutError as e:
    print(f"\n⏱️  Timeout error: Operation took longer than {client.timeout}s")
    print("💡 Tip: Increase timeout or simplify the request")
except anthropic.BadRequestError as e:
    print(f"\n❌ Bad request error: {e}")
    if "credit balance" in str(e).lower():
        print("💡 Tip: Add credits at https://console.anthropic.com/settings/plans")
    elif "skill" in str(e).lower():
        print("💡 Tip: Check that the skill_id exists and is accessible")
except anthropic.RateLimitError as e:
    print(f"\n⚠️  Rate limit error: {e}")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")