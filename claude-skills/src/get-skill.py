import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

client = anthropic.Anthropic()

skill = client.beta.skills.retrieve("pptx",
    betas=["skills-2025-10-02"],
)

print(skill)