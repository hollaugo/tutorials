import asyncio
from agent2agent.app.client import ask_agent

if __name__ == "__main__":
    response = asyncio.run(ask_agent("Get me Apple stock summary"))
    print(response) 