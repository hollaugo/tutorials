import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

client = anthropic.Anthropic()

# Collect all skills across pages
all_skills = []

# Get first page
page = client.beta.skills.list(betas=["skills-2025-10-02"])
all_skills.extend(page.data)

# Loop through remaining pages
while page.has_more:
    page = client.beta.skills.list(
        betas=["skills-2025-10-02"],
        after=page.next_page
    )
    all_skills.extend(page.data)

# Print all skills in a readable format
print(f"\nFound {len(all_skills)} skills:\n")
for skill in all_skills:
    print(f"• {skill.display_title} (ID: {skill.id})")
    print(f"  Version: {skill.latest_version}")
    print(f"  Source: {skill.source}")
    print(f"  Updated: {skill.updated_at}\n")
