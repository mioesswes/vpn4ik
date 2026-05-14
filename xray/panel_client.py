import json
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx

from backend.node_config import NodeRuntimeConfig


@dataclass(slots=True)
class XrayPanelSession:
    node: NodeRuntimeConfig
    client: httpx.AsyncClient


class XrayPanelClient:
    def __init__(self, node: NodeRuntimeConfig) -> None:
        self.node = node

    def _base_url(self) -> str:
        if not self.node.panel_url:
            raise ValueError(f"Panel URL is not configured for node {self.node.location.value}.")
        return self.node.panel_url.rstrip("/")

    def _panel_origin(self) -> str:
        parts = urlsplit(self._base_url())
        return f"{parts.scheme}://{parts.netloc}"

    async def _build_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._panel_origin(),
            timeout=httpx.Timeout(20.0),
            verify=False,
            follow_redirects=True,
        )

    def _path(self, suffix: str) -> str:
        base = urlsplit(self._base_url()).path.rstrip("/")
        return f"{base}/{suffix.lstrip('/')}"

    @staticmethod
    def _decode_json(response: httpx.Response) -> dict:
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        if isinstance(payload, dict) and payload.get("success") is False:
            message = payload.get("msg") or payload.get("message") or "3x-ui request failed"
            raise ValueError(message)
        return payload if isinstance(payload, dict) else {"data": payload}

    async def login(self) -> XrayPanelSession:
        if not self.node.panel_username or not self.node.panel_password:
            raise ValueError(f"Panel credentials are not configured for node {self.node.location.value}.")

        client = await self._build_client()
        response = await client.post(
            self._path("login"),
            data={
                "username": self.node.panel_username,
                "password": self.node.panel_password,
            },
        )
        response.raise_for_status()
        return XrayPanelSession(node=self.node, client=client)

    async def list_inbounds(self) -> dict:
        session = await self.login()
        try:
            response = await session.client.post(self._path("panel/api/inbounds/list"))
            response.raise_for_status()
            return self._decode_json(response)
        finally:
            await session.client.aclose()

    async def get_inbound(self) -> dict:
        if not self.node.inbound_id:
            raise ValueError(f"Inbound ID is not configured for node {self.node.location.value}.")
        session = await self.login()
        try:
            response = await session.client.post(
                self._path(f"panel/api/inbounds/get/{self.node.inbound_id}")
            )
            response.raise_for_status()
            return self._decode_json(response)
        finally:
            await session.client.aclose()

    async def add_client(self, email: str, uuid: str, limit_ip: int, flow: str = "xtls-rprx-vision") -> dict:
        if not self.node.inbound_id:
            raise ValueError(f"Inbound ID is not configured for node {self.node.location.value}.")
        session = await self.login()
        try:
            payload = {
                "id": int(self.node.inbound_id),
                "settings": json.dumps(
                    {
                        "clients": [
                            {
                                "id": uuid,
                                "flow": flow,
                                "email": email,
                                "limitIp": limit_ip,
                                "enable": True,
                            }
                        ]
                    }
                ),
            }
            response = await session.client.post(
                self._path("panel/api/inbounds/addClient"),
                json=payload,
            )
            response.raise_for_status()
            return self._decode_json(response)
        finally:
            await session.client.aclose()

    async def update_client(self, email: str, uuid: str, limit_ip: int, flow: str = "xtls-rprx-vision") -> dict:
        if not self.node.inbound_id:
            raise ValueError(f"Inbound ID is not configured for node {self.node.location.value}.")
        session = await self.login()
        try:
            payload = {
                "id": int(self.node.inbound_id),
                "settings": json.dumps(
                    {
                        "clients": [
                            {
                                "id": uuid,
                                "flow": flow,
                                "email": email,
                                "limitIp": limit_ip,
                                "enable": True,
                            }
                        ]
                    }
                ),
            }
            response = await session.client.post(
                self._path("panel/api/inbounds/updateClient"),
                json=payload,
            )
            response.raise_for_status()
            return self._decode_json(response)
        finally:
            await session.client.aclose()

    async def upsert_client(self, email: str, uuid: str, limit_ip: int) -> dict:
        try:
            return await self.add_client(email=email, uuid=uuid, limit_ip=limit_ip)
        except ValueError as exc:
            message = str(exc).lower()
            if "exist" not in message and "duplicate" not in message and "email" not in message:
                raise
            return await self.update_client(email=email, uuid=uuid, limit_ip=limit_ip)

    async def delete_client(self, email: str) -> dict:
        if not self.node.inbound_id:
            raise ValueError(f"Inbound ID is not configured for node {self.node.location.value}.")
        session = await self.login()
        try:
            response = await session.client.post(
                self._path(f"panel/api/inbounds/{self.node.inbound_id}/delClient/{email}")
            )
            response.raise_for_status()
            return self._decode_json(response)
        finally:
            await session.client.aclose()
