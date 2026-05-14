from urllib.parse import quote

from backend.config import Settings
from backend.enums import NodeLocation
from backend.node_config import NodeRuntimeConfig, build_node_configs
from xray.panel_client import XrayPanelClient


class XrayService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.nodes = build_node_configs(settings)

    def get_node(self, location: NodeLocation) -> NodeRuntimeConfig:
        return self.nodes[location]

    def get_panel_client(self, location: NodeLocation) -> XrayPanelClient:
        node = self.get_node(location)
        if not node.panel_ready:
            raise ValueError(f"Panel access is not fully configured for node {location.value}.")
        return XrayPanelClient(node)

    @staticmethod
    def build_client_email(user_id: int) -> str:
        return f"tg-{user_id}"

    async def ensure_client(self, user_id: int, location: NodeLocation, device_limit: int) -> None:
        client = self.get_panel_client(location)
        await client.upsert_client(
            email=self.build_client_email(user_id),
            uuid=self.settings.xray_shared_uuid,
            limit_ip=device_limit,
        )

    async def delete_client(self, user_id: int, location: NodeLocation) -> None:
        client = self.get_panel_client(location)
        try:
            await client.delete_client(email=self.build_client_email(user_id))
        except ValueError as exc:
            message = str(exc).lower()
            if "not found" in message or "failed to find" in message or "email" in message:
                return
            raise

    async def reprovision_client(
        self,
        user_id: int,
        old_location: NodeLocation | None,
        new_location: NodeLocation,
        device_limit: int,
    ) -> None:
        if old_location and old_location != new_location:
            await self.delete_client(user_id=user_id, location=old_location)
        await self.ensure_client(user_id=user_id, location=new_location, device_limit=device_limit)

    async def generate_vless_reality_config(self, user_id: int, location: NodeLocation) -> str:
        node = self.get_node(location)
        if not node.ready_for_config:
            raise ValueError(
                f"Node {location.value} is missing Reality parameters. Fill .env before issuing configs."
            )
        label = quote(f"user-{user_id}-{location.value}")
        return (
            "vless://"
            f"{self.settings.xray_shared_uuid}@{node.public_host}:{node.public_port}"
            "?security=reality"
            "&type=tcp"
            "&headerType=none"
            "&flow=xtls-rprx-vision"
            "&encryption=none"
            "&fp=chrome"
            f"&pbk={node.reality_public_key}"
            f"&sni={node.reality_server_name}"
            f"&sid={node.reality_short_id}"
            "&spx=%2F"
            f"#{label}"
        )

    async def switch_user_location(self, user_id: int, old_location: NodeLocation, location: NodeLocation, device_limit: int) -> str:
        await self.reprovision_client(
            user_id=user_id,
            old_location=old_location,
            new_location=location,
            device_limit=device_limit,
        )
        return await self.generate_vless_reality_config(user_id=user_id, location=location)
