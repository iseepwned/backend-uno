import json
from fastapi import WebSocket
from typing import Dict


class LobbyManager:
    def __init__(self):
        # {player_name:websocket}
        self.active_connections: Dict[str:WebSocket] = {}

    async def connect(self, player_name: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[player_name] = websocket

    async def disconnect(self, player_name: str):
        await self.active_connections[player_name].close()
        self.active_connections.pop(player_name)

    async def destroy(self):
        for websocket in self.active_connections.values():
            await websocket.close()
        self.active_connections.clear()

    async def send_personal_message(self, message: dict, player_name: str):
        await self.active_connections[player_name].send_text(json.dumps(message))

    async def broadcast(self, message: dict, player_name_ignore: str | None = None):
        for player_name, websocket in self.active_connections.items():
            if player_name != player_name_ignore:
                await websocket.send_text(json.dumps(message))


# {match_id:LobbyManager}
lobbys: Dict[int, LobbyManager] = {}