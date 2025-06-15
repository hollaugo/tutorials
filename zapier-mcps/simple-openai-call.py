from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1",
    input="Run the Salesforce: Convert Lead to Contact tool",
    tool_choice="required",
    tools=[
        {
            "type": "mcp",
            "server_label": "zapier",
            "server_url": "https://mcp.zapier.com/api/mcp/mcp",
            "require_approval": "never",
            "headers": {
                "Authorization": f"Bearer {os.getenv('ZAPIER_API_KEY')}",
            },
        }
    ],
)

print(response)