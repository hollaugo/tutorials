from fastapi import FastAPI, Request
from slack_bolt.async_app import AsyncApp, AsyncAssistant, AsyncSetStatus, AsyncSay, AsyncAck
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_sdk.web.async_client import AsyncWebClient
import os
import json
import logging
from langgraph_agent.agent import ask_agent
from dotenv import load_dotenv

load_dotenv()

# Initialize Slack app with bot message handling enabled
app = AsyncApp(
    token=os.environ["SLACK_BOT_TOKEN"],
    # Enable handling of bot messages for dropdown interactions
    ignoring_self_assistant_message_events_enabled=False,
)

# Create assistant
assistant = AsyncAssistant()
app.assistant(assistant)

@assistant.thread_started
async def handle_thread_started(say: AsyncSay):
    """Handle when a new thread is started with the assistant."""
    await say(
        text="Hi! I'm your Bright Data assistant. Please select which AI system you'd like to use:",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hi! I'm your Bright Data assistant. Please select which AI system you'd like to use:"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Choose your preferred AI system:"
                },
                "accessory": {
                    "type": "static_select",
                    "action_id": "select_ai_system",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select AI system"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "LangGraph (Current)"
                            },
                            "value": "langgraph"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "ADK (New)"
                            },
                            "value": "adk"
                        }
                    ]
                }
            }
        ]
    )

@assistant.user_message
async def handle_user_message(
    message,
    set_status: AsyncSetStatus,
    say: AsyncSay,
    client: AsyncWebClient,
    context,
    logger: logging.Logger,
):
    """Handle user messages in assistant threads."""
    try:
        # Set typing indicator
        await set_status("is typing...")
        
        # Get the user's message text
        user_message = message.get("text", "")
        
        if not user_message:
            await say("I didn't receive any text in your message. Could you please try again?")
            return
        
        # Check thread history to find AI system selection
        ai_system = "langgraph"  # default
        try:
            replies = await client.conversations_replies(
                channel=context.channel_id,
                ts=context.thread_ts,
                oldest=context.thread_ts,
                limit=20,
            )
            
            # Look for bot messages with metadata indicating AI system selection
            for msg in replies.get("messages", []):
                if msg.get("bot_id") and msg.get("metadata"):
                    metadata = msg.get("metadata", {})
                    if metadata.get("event_type") == "ai_system_selected":
                        ai_system = metadata.get("event_payload", {}).get("ai_system", "langgraph")
                        break
        except Exception as e:
            logger.warning(f"Could not retrieve AI system selection: {e}")
            # If we can't determine the AI system, default to langgraph
            pass
        
        # Create thread ID from Slack thread timestamp
        thread_id = f"slack_{context.channel_id}_{context.thread_ts}"
        
        # Get recent conversation history from Slack thread (optional fallback)
        conversation_history = []
        try:
            # Get last few messages for context continuity
            recent_replies = await client.conversations_replies(
                channel=context.channel_id,
                ts=context.thread_ts,
                oldest=context.thread_ts,
                limit=10,
            )
            
            # Convert Slack messages to conversation format
            for msg in recent_replies.get("messages", []):
                if msg.get("text") and msg.get("text") != user_message:  # Skip current message
                    role = "assistant" if msg.get("bot_id") else "user"
                    conversation_history.append({
                        "role": role,
                        "content": msg["text"]
                    })
        except Exception as e:
            logger.warning(f"Could not retrieve conversation history: {e}")
            # If we can't get history, continue without it
            pass
        
        # Route to appropriate AI system
        if ai_system == "adk":
            # Use ADK agent with extended timeout
            from adk_agent.agent import ask_adk_agent
            response = await ask_adk_agent(
                user_message, 
                origin="slack", 
                thread_id=thread_id,
                conversation_history=conversation_history
            )
        else:
            # Use LangGraph 
            response = await ask_agent(
                user_message, 
                origin="slack", 
                thread_id=thread_id,
                conversation_history=conversation_history
            )
        
        # Send response back to Slack
        await say(response)
        
        # Clear the typing status
        await set_status("")
        
    except Exception as e:
        logger.exception(f"Error in handle_user_message: {e}")
        await say(f"Sorry, I encountered an error while processing your request: {str(e)}")
        await set_status("")

# Handle dropdown selection for AI system
@app.action("select_ai_system")
async def handle_ai_system_selection(ack: AsyncAck, body: dict, client: AsyncWebClient):
    """Handle AI system selection from dropdown."""
    await ack()
    
    selected_value = body["actions"][0]["selected_option"]["value"]
    channel_id = body["channel"]["id"]
    thread_ts = body["message"]["thread_ts"]
    
    # Post a message with metadata to trigger the bot_message handler
    await client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text=f"Great! You've selected **{selected_value.upper()}**. Now you can ask me anything about web scraping, data collection, and proxy management.",
        metadata={
            "event_type": "ai_system_selected",
            "event_payload": {"ai_system": selected_value}
        }
    )

# Handle bot messages with metadata
@assistant.bot_message
async def handle_bot_message(payload: dict, say: AsyncSay):
    """Handle bot messages with structured metadata."""
    try:
        metadata = payload.get("metadata", {})
        event_type = metadata.get("event_type")
        
        if event_type == "ai_system_selected":
            # AI system has been selected, ready for user questions
            # The metadata is now stored and will be used in user_message handler
            pass
        
    except Exception as e:
        await say(f"Sorry, I encountered an error: {str(e)}")

# FastAPI setup
api = FastAPI()
handler = AsyncSlackRequestHandler(app)

@api.post("/slack/events")
async def endpoint(req: Request):
    """Handle Slack events."""
    return await handler.handle(req)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8010))
    print(f"Starting Slack bot server on port {port}")
    uvicorn.run(api, host="0.0.0.0", port=port)