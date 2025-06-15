from fastapi import FastAPI, Request
from slack_bolt.async_app import AsyncApp, AsyncAssistant, AsyncSetStatus, AsyncSay
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
import os
import sys
from app.client import ask_agent
from dotenv import load_dotenv

load_dotenv()
                                                                                    
# --- SLACK SETUP ---
slack_app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])
slack_handler = AsyncSlackRequestHandler(slack_app)
assistant = AsyncAssistant()
slack_app.use(assistant)

@assistant.thread_started
async def start_thread(say: AsyncSay):
    await say(":wave: Hi! I'm your Investment Research Analyst Agent. Ask me about stocks, SEC filings, analyst recommendations, or anything related to investment research!")

@assistant.user_message
async def respond_in_thread(payload, logger, set_status: AsyncSetStatus, say: AsyncSay, client, body, ack):
    await set_status("is typing...")
    user_text = payload["text"]
    print("Received from Slack:", user_text)
    try:
        agent_result = await ask_agent(user_text, origin="slack")
        main_message = agent_result["message"]
        context_steps = agent_result["context"]
        raw_metadata = agent_result.get("metadata", {})

        # Prepare metadata for Slack (event_type + event_payload)
        event_type = "investment_agent_response"
        event_payload = {
            "raw_agent_output": raw_metadata,
            "steps": context_steps
        }
        import json
        # Slack metadata limit is 4KB (4096 bytes)
        meta_json = json.dumps(event_payload)
        if len(meta_json.encode("utf-8")) > 4000:
            # TODO: Store in cache/db and use a reference key
            event_payload = {"reference_key": "TO_BE_IMPLEMENTED"}

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Investment Research Analyst*\n{main_message}"
                }
            },
            {"type": "divider"}
        ]
        for idx, step in enumerate(context_steps):
            label = f":mag: *Step {idx+1}*"
            blocks.append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"{label}: {step}"}
                ]
            })
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "See Metadata"},
                    "action_id": "show_metadata",
                    "value": "show_metadata"
                }
            ]
        })
        # Send message with metadata
        await say(
            blocks=blocks,
            text=main_message,
            metadata={
                "event_type": event_type,
                "event_payload": event_payload
            }
        )
    except Exception as e:
        logger.exception(f"Failed to respond to an inquiry: {e}")
        await say(f":warning: Sorry, something went wrong while processing your investment research request (error: {e})")

# --- MODAL HANDLER FOR METADATA BUTTON ---
@slack_app.action("show_metadata")
async def handle_show_metadata(ack, body, client, logger):
    await ack()
    try:
        metadata = None
        if "message" in body and "metadata" in body["message"]:
            meta = body["message"]["metadata"]
            # Slack delivers event_type and event_payload
            metadata = meta.get("event_payload")
        if not metadata:
            metadata = {"error": "No metadata found for this message."}
        import json
        pretty_metadata = json.dumps(metadata, indent=2)[:2900]  # Slack modal limit
        # Show steps separately if present
        steps = metadata.get("steps") if isinstance(metadata, dict) else None
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Raw Agent Output & Metadata:*\n```{pretty_metadata}```"
                }
            }
        ]
        if steps:
            blocks.append({
                "type": "divider"
            })
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Agent Steps:*\n" + "\n".join([f"*Step {i+1}:* {s}" for i, s in enumerate(steps)])
                }
            })
        await client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "Agent Metadata"},
                "close": {"type": "plain_text", "text": "Close"},
                "blocks": blocks
            }
        )
    except Exception as e:
        logger.exception(f"Failed to open metadata modal: {e}")

# Add a generic event handler for debugging
@slack_app.event("message")
async def handle_message_events(body, say):
    print("Generic message event:", body)
    await say("Hello from generic handler!")

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