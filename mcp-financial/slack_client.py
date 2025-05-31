from fastapi import FastAPI, Request
from slack_bolt.async_app import AsyncApp, AsyncAssistant, AsyncSetStatus, AsyncSay
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
import os
import sys
from client import ask_agent
from dotenv import load_dotenv

load_dotenv()
                                                                                    
# --- SLACK SETUP ---
slack_app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])
slack_handler = AsyncSlackRequestHandler(slack_app)
assistant = AsyncAssistant()
slack_app.use(assistant)

@assistant.thread_started
async def start_thread(say: AsyncSay):
    await say(":wave: Hi, how can I help you today?")

@assistant.user_message
async def respond_in_thread(payload, logger, set_status: AsyncSetStatus, say: AsyncSay):
    await set_status("is typing...")
    user_text = payload["text"]
    try:
        agent_response = await ask_agent(user_text, origin="slack")
        await say(agent_response)
    except Exception as e:
        logger.exception(f"Failed to respond to an inquiry: {e}")
        await say(f":warning: Sorry, something went wrong during processing your request (error: {e})")

# --- FASTAPI APP FOR SLACK EVENTS ---
app = FastAPI()

@app.post("/slack/events")
async def endpoint(req: Request):
    try:
        return await slack_handler.handle(req)
    except Exception as e:
        print(f"[ERROR] Exception in /slack/events: {e}", file=sys.stderr)
        raise

# --- RUN ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8010))
    uvicorn.run(app, host="0.0.0.0", port=port) 