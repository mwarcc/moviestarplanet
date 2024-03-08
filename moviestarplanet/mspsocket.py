import asyncio
import json
import aiohttp
import websockets

class MspSocketUser:
    def __init__(self):
        self.websocket = None
        self.connected = False
        self.ping_id = 0
        self.session = aiohttp.ClientSession()

    async def connect(self, server):
        self.websocket_path = await self.get_web_socket_url(server)
        uri = f"ws://{self.websocket_path.replace('-', '.')}:{10843}/{self.websocket_path.replace('.', '-')}/?transport=websocket"
        self.websocket = await websockets.connect(uri)
        self.connected = True
        asyncio.create_task(self.send_ping())

    async def send_ping(self):
        """
        Sends a ping message to the server every 5 seconds.
        """
        await asyncio.sleep(5)
        ping_message = { "pingId": self.ping_id, "messageType": 500}
        await self.websocket.send(f"42[\"500\",{json.dumps(ping_message)}]")
        self.ping_id += 1

    async def wait_is_connected(self):
        while self.websocket is None or not self.websocket.open:
            await asyncio.sleep(0.1)

    async def on_message(self, message):
        if message.startswith("42"):
            message_parsed = json.loads(message[2:])
            if message_parsed[1].get("messageType") == 11 and message_parsed[1]["messageContent"].get("success"):
                if hasattr(self, "on_connected"):
                    self.on_connected()

    async def send_authentication(self, server, access_token, profile_id):
        await self.wait_is_connected()
        auth_message = {
            "messageContent": {
                "country": server.upper(),
                "version": 1,
                "access_token": access_token,
                "applicationId": "APPLICATION_WEB",
                "username": profile_id
            },
            "senderProfileId": None,
            "messageType": 10
        }
        await self.websocket.send('42["10",{}]'.format(json.dumps(auth_message)))

    async def get_web_socket_url(self, server):
        url = "https://presence.mspapis.com/getServer"
        if server == "US":
            url = "https://presence-us.mspapis.com/getServer"
        async with self.session.get(url) as response:
            return await response.text()