import anthropic
from anthropic.lib import files_from_dir
from dotenv import load_dotenv
import os

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print("Creating skill from directory...")
skill = client.beta.skills.create(
    betas=["skills-2025-10-02"],
    display_title="Apps SDK Builder",
    files=files_from_dir("custom-skills/openai-apps-sdk/openai-apps-sdk-builder"),
)
print(f"✅ Skill created successfully!")
print(f"ID: {skill.id}")
print(f"Display Title: {skill.display_title}")
print(f"Version: {skill.latest_version}")
