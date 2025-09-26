from typing import Any, Dict

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for chat updates in real-time.

    Usage:
    - Connect to: ws://<host>/ws/chat/<session_id>/
    - Backend broadcasts events with type "chat.message" to the group "chat_<session_id>"
    """

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.group_name = f"chat_{self.session_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"event": "connected", "session_id": self.session_id})

    async def disconnect(self, close_code: int):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content: Dict[str, Any], **kwargs):
        """
        Client messages can be used for ping or custom operations later.
        """
        await self.send_json({"event": "echo", "payload": content})

    async def chat_message(self, event: Dict[str, Any]):
        """
        Handler used by group_send via type='chat.message'
        """
        await self.send_json(
            {
                "event": event.get("event", "update"),
                "payload": event.get("payload", {}),
            }
        )
