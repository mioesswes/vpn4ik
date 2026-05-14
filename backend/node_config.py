from dataclasses import dataclass

from backend.config import Settings
from backend.enums import NodeLocation


@dataclass(slots=True)
class NodeRuntimeConfig:
    location: NodeLocation
    public_host: str
    public_port: int
    reality_public_key: str | None
    reality_short_id: str | None
    reality_server_name: str | None
    panel_url: str | None
    panel_username: str | None
    panel_password: str | None
    inbound_id: str | None

    @property
    def ready_for_config(self) -> bool:
        return bool(
            self.public_host
            and self.reality_public_key
            and self.reality_short_id
            and self.reality_server_name
        )

    @property
    def panel_ready(self) -> bool:
        return bool(self.panel_url and self.panel_username and self.panel_password and self.inbound_id)


def build_node_configs(settings: Settings) -> dict[NodeLocation, NodeRuntimeConfig]:
    return {
        NodeLocation.GERMANY: NodeRuntimeConfig(
            location=NodeLocation.GERMANY,
            public_host=settings.xray_germany_public_host,
            public_port=settings.xray_germany_public_port,
            reality_public_key=settings.xray_germany_reality_public_key,
            reality_short_id=settings.xray_germany_reality_short_id,
            reality_server_name=settings.xray_germany_reality_server_name,
            panel_url=settings.xray_germany_panel_url,
            panel_username=settings.xray_germany_panel_username,
            panel_password=settings.xray_germany_panel_password,
            inbound_id=settings.xray_germany_inbound_id,
        ),
        NodeLocation.SWEDEN: NodeRuntimeConfig(
            location=NodeLocation.SWEDEN,
            public_host=settings.xray_sweden_public_host,
            public_port=settings.xray_sweden_public_port,
            reality_public_key=settings.xray_sweden_reality_public_key,
            reality_short_id=settings.xray_sweden_reality_short_id,
            reality_server_name=settings.xray_sweden_reality_server_name,
            panel_url=settings.xray_sweden_panel_url,
            panel_username=settings.xray_sweden_panel_username,
            panel_password=settings.xray_sweden_panel_password,
            inbound_id=settings.xray_sweden_inbound_id,
        ),
        NodeLocation.FINLAND: NodeRuntimeConfig(
            location=NodeLocation.FINLAND,
            public_host=settings.xray_finland_public_host,
            public_port=settings.xray_finland_public_port,
            reality_public_key=settings.xray_finland_reality_public_key,
            reality_short_id=settings.xray_finland_reality_short_id,
            reality_server_name=settings.xray_finland_reality_server_name,
            panel_url=settings.xray_finland_panel_url,
            panel_username=settings.xray_finland_panel_username,
            panel_password=settings.xray_finland_panel_password,
            inbound_id=settings.xray_finland_inbound_id,
        ),
        NodeLocation.USA: NodeRuntimeConfig(
            location=NodeLocation.USA,
            public_host=settings.xray_usa_public_host,
            public_port=settings.xray_usa_public_port,
            reality_public_key=settings.xray_usa_reality_public_key,
            reality_short_id=settings.xray_usa_reality_short_id,
            reality_server_name=settings.xray_usa_reality_server_name,
            panel_url=settings.xray_usa_panel_url,
            panel_username=settings.xray_usa_panel_username,
            panel_password=settings.xray_usa_panel_password,
            inbound_id=settings.xray_usa_inbound_id,
        ),
    }
