from slack_bolt.async_app import AsyncApp, AsyncAssistant, AsyncSetStatus, AsyncSay
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_sdk.web.async_client import AsyncWebClient
import os
import logging
import importlib.util
import sys
from dotenv import load_dotenv
from slack_formatter import to_slack_mrkdwn, to_slack_blocks

# Import the module with hyphens in filename
spec = importlib.util.spec_from_file_location("langgraph_agent_client", "langgraph-agent-client.py")
langgraph_agent_client = importlib.util.module_from_spec(spec)
sys.modules["langgraph_agent_client"] = langgraph_agent_client
spec.loader.exec_module(langgraph_agent_client)
ask_agent = langgraph_agent_client.ask_agent

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
        text="Hi! I'm your Notion assistant. I can help you with Notion tasks like creating pages, updating databases, and searching your workspace. What would you like to do?",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hi! I'm your Notion assistant. I can help you with:"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "• Create pages and databases\n• Update existing content\n• Search your workspace\n• Manage tasks and projects\n\nJust ask me what you'd like to do!"
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
        
        # Create thread ID from Slack thread timestamp
        thread_id = f"slack_{context.channel_id}_{context.thread_ts}"
        
        # Get comprehensive conversation history from Slack thread
        conversation_history = []
        try:
            # Get all messages in the thread for full context (limit 50 to avoid token limits)
            recent_replies = await client.conversations_replies(
                channel=context.channel_id,
                ts=context.thread_ts,
                oldest=context.thread_ts,
                limit=50,
                inclusive=True  # Include the original message
            )
            
            # Convert Slack messages to conversation format, maintaining chronological order
            messages = recent_replies.get("messages", [])
            for msg in messages:
                # Skip empty messages, file uploads, and other non-text content
                if not msg.get("text") or not msg.get("text").strip():
                    continue
                    
                # Determine role - assistant for bot messages, user for human messages
                if msg.get("bot_id") or msg.get("app_id"):
                    role = "assistant"
                else:
                    role = "user"
                
                # Clean up the message text (remove Slack formatting if needed)
                content = msg["text"]
                
                # Add to conversation history
                conversation_history.append({
                    "role": role,
                    "content": content,
                    "timestamp": msg.get("ts", "")
                })
            
            # Remove the current message from history since it will be added as the new user message
            if conversation_history and conversation_history[-1]["content"] == user_message:
                conversation_history.pop()
            
            logger.info(f"Retrieved {len(conversation_history)} messages from thread history")
            
        except Exception as e:
            logger.warning(f"Could not retrieve conversation history: {e}")
            # If we can't get history, continue without it
            pass
        
        # Use LangGraph agent
        response = await ask_agent(
            user_message, 
            origin="slack", 
            thread_id=thread_id,
            conversation_history=conversation_history
        )
        
        # Format response for Slack before sending
        try:
            # Convert markdown to Slack mrkdwn format
            formatted_response = to_slack_mrkdwn(response)
            
            # For long responses, use blocks for better formatting
            if len(formatted_response) > 2000:
                blocks = to_slack_blocks(response)
                await say(blocks=blocks)
            else:
                # For shorter responses, use simple text with mrkdwn formatting
                await say(formatted_response)
                
        except Exception as format_error:
            logger.warning(f"Failed to format response: {format_error}")
            # Fallback to original response if formatting fails
            await say(response)
        
        # Clear the typing status
        await set_status("")
        
    except Exception as e:
        logger.exception(f"Error in handle_user_message: {e}")
        await say(f"Sorry, I encountered an error while processing your request: {str(e)}")
        await set_status("")

# Handle bot messages with metadata (needed for proper assistant functionality)
@assistant.bot_message
async def handle_bot_message(payload: dict, say: AsyncSay):
    """Handle bot messages with structured metadata."""
    try:
        metadata = payload.get("metadata", {})
        event_type = metadata.get("event_type")
        
        if event_type == "system_ready":
            # System is ready for user questions
            pass
        
    except Exception as e:
        await say(f"Sorry, I encountered an error: {str(e)}")

async def main():
    """Main function to start the Slack app in Socket Mode"""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create socket mode handler
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    
    print("Starting Notion MCP Slack bot in Socket Mode...")
    await handler.start_async()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())