import json
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx

from backend.node_config import NodeRuntimeConfig


@dataclass(slots=True)
class XrayPanelSession:
    node: NodeRuntimeConfig
    client: httpx.AsyncClient
    api_prefixes: list[str]


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

    def _panel_path(self) -> str:
        raw_path = urlsplit(self._base_url()).path.rstrip("/")
        return raw_path or ""

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value not in seen:
                result.append(value)
                seen.add(value)
        return result

    def _base_path_candidates(self) -> list[str]:
        panel_path = self._panel_path()
        candidates = [panel_path]
        if panel_path.endswith("/panel"):
            candidates.append(panel_path[: -len("/panel")])
        elif panel_path:
            candidates.append(f"{panel_path}/panel")
        candidates.extend(["/panel", ""])
        normalized = [candidate.rstrip("/") for candidate in candidates]
        normalized = [candidate if candidate else "" for candidate in normalized]
        return self._unique(normalized)

    def _login_candidates(self) -> list[tuple[str, str]]:
        candidates: list[tuple[str, str]] = []
        for base_path in self._base_path_candidates():
            if base_path.endswith("/panel"):
                candidates.append((base_path, f"{base_path}/login"))
            else:
                candidates.append((base_path, f"{base_path}/login"))
                candidates.append((base_path, f"{base_path}/panel/login"))
        return self._unique([f"{base}|{login}" for base, login in candidates])

    def _decode_login_candidates(self) -> list[tuple[str, str]]:
        return [tuple(item.split("|", 1)) for item in self._login_candidates()]

    async def _build_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._panel_origin(),
            timeout=httpx.Timeout(20.0),
            verify=False,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 TelegramVPNBot/1.0",
                "Accept": "application/json, text/plain, */*",
            },
        )

    @staticmethod
    def _is_json_response(response: httpx.Response) -> bool:
        content_type = response.headers.get("content-type", "")
        return "json" in content_type.lower()

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

    @staticmethod
    def _login_success(response: httpx.Response) -> bool:
        if response.status_code in (200, 204, 302, 303):
            if XrayPanelClient._is_json_response(response):
                try:
                    payload = response.json()
                except ValueError:
                    payload = {}
                if isinstance(payload, dict) and payload.get("success") is False:
                    return False
            return True
        return False

    @staticmethod
    def _join(prefix: str, suffix: str) -> str:
        prefix = prefix.rstrip("/")
        suffix = suffix.lstrip("/")
        if not prefix:
            return f"/{suffix}"
        return f"{prefix}/{suffix}"

    async def _warmup(self, client: httpx.AsyncClient, base_path: str, login_path: str) -> None:
        for candidate in self._unique([base_path, login_path]):
            if not candidate:
                continue
            try:
                await client.get(candidate)
            except httpx.HTTPError:
                continue

    def _api_prefix_candidates(self, base_path: str, login_path: str) -> list[str]:
        prefixes = [
            self._join(base_path, "panel/api"),
            self._join(base_path, "api"),
            self._join(self._panel_path(), "panel/api"),
            self._join(self._panel_path(), "api"),
            "/panel/api",
            "/api",
        ]
        if login_path.endswith("/panel/login"):
            panel_root = login_path[: -len("/login")]
            prefixes.insert(0, self._join(panel_root, "api"))
        return self._unique(prefixes)

    async def login(self) -> XrayPanelSession:
        if not self.node.panel_username or not self.node.panel_password:
            raise ValueError(f"Panel credentials are not configured for node {self.node.location.value}.")

        last_error: Exception | None = None
        for base_path, login_path in self._decode_login_candidates():
            client = await self._build_client()
            try:
                await self._warmup(client, base_path=base_path, login_path=login_path)
                response = await client.post(
                    login_path,
                    data={
                        "username": self.node.panel_username,
                        "password": self.node.panel_password,
                    },
                    headers={
                        "Origin": self._panel_origin(),
                        "Referer": f"{self._panel_origin()}{login_path}",
                    },
                )
                if self._login_success(response):
                    return XrayPanelSession(
                        node=self.node,
                        client=client,
                        api_prefixes=self._api_prefix_candidates(base_path=base_path, login_path=login_path),
                    )
                last_error = httpx.HTTPStatusError(
                    f"Login failed with status {response.status_code}",
                    request=response.request,
                    response=response,
                )
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
            await client.aclose()

        if last_error is None:
            raise ValueError(f"Unable to authenticate to 3x-ui for node {self.node.location.value}.")
        raise last_error

    async def _request_api(
        self,
        session: XrayPanelSession,
        suffix: str,
        *,
        json_payload: dict | None = None,
    ) -> dict:
        last_error: Exception | None = None
        for prefix in session.api_prefixes:
            path = self._join(prefix, suffix)
            try:
                response = await session.client.post(path, json=json_payload)
                response.raise_for_status()
                return self._decode_json(response)
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
        if last_error is None:
            raise ValueError(f"Unable to call 3x-ui API for node {self.node.location.value}.")
        raise last_error

    async def list_inbounds(self) -> dict:
        session = await self.login()
        try:
            return await self._request_api(session, "inbounds/list")
        finally:
            await session.client.aclose()

    async def get_inbound(self) -> dict:
        if not self.node.inbound_id:
            raise ValueError(f"Inbound ID is not configured for node {self.node.location.value}.")
        session = await self.login()
        try:
            return await self._request_api(session, f"inbounds/get/{self.node.inbound_id}")
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
            return await self._request_api(session, "inbounds/addClient", json_payload=payload)
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
            return await self._request_api(session, "inbounds/updateClient", json_payload=payload)
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
            return await self._request_api(session, f"inbounds/{self.node.inbound_id}/delClient/{email}")
        finally:
            await session.client.aclose()
