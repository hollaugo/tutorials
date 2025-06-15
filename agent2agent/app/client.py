import os
from uuid import uuid4
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'

async def ask_agent(user_text: str, origin: str = "slack") -> dict:
    base_url = os.environ.get("AGENT_SERVER_URL", "http://localhost:10000")
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        agent_card = await resolver.get_agent_card()
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        send_message_payload = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': user_text}
                ],
                'messageId': uuid4().hex,
            },
        }
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )
        response = await client.send_message(request)
        # Extract the main message
        try:
            # Try to extract from artifacts (preferred)
            if hasattr(response.root.result, 'artifacts') and response.root.result.artifacts:
                artifact = response.root.result.artifacts[0]
                part = None
                # Attribute access for parts
                if hasattr(artifact, 'parts') and artifact.parts:
                    part = artifact.parts[0]
                elif isinstance(artifact, dict) and 'parts' in artifact and artifact['parts']:
                    part = artifact['parts'][0]
                # Now get text from part
                if part is not None:
                    # If part is a wrapper/root, get .root if present
                    if hasattr(part, 'root') and part.root:
                        root = part.root
                        if hasattr(root, 'text'):
                            main_text = root.text
                        elif isinstance(root, dict) and 'text' in root:
                            main_text = root['text']
                        else:
                            main_text = str(root)
                    elif hasattr(part, 'text'):
                        main_text = part.text
                    elif isinstance(part, dict) and 'text' in part:
                        main_text = part['text']
                    else:
                        main_text = str(part)
                else:
                    main_text = str(artifact)
            else:
                main_text = response.root.result.parts[0].text
        except Exception:
            main_text = str(response.model_dump(mode='json', exclude_none=True))
        # Extract step-by-step context if available
        context_steps = []
        if hasattr(response.root.result, 'history'):
            for item in response.root.result.history:
                if 'parts' in item and item['parts']:
                    for part in item['parts']:
                        if part.get('kind') == 'text':
                            context_steps.append(part.get('text'))
        return {
            "message": main_text,
            "context": context_steps,
            "metadata": response.model_dump(mode='json', exclude_none=True)
        } 