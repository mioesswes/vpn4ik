from backend.config import Settings
from backend.enums import NodeLocation
from xray.service import XrayService


class MonitoringService:
    def __init__(self, settings: Settings, xray: XrayService) -> None:
        self.settings = settings
        self.xray = xray

    async def node_summary(self) -> list[str]:
        summaries: list[str] = []
        for location in NodeLocation:
            node = self.xray.get_node(location)
            if node.ready_for_config and node.panel_ready:
                status = "ready"
            elif node.ready_for_config:
                status = "config_only"
            else:
                status = "config_missing"
            summaries.append(f"{location.value}: {status}")
        return summaries

    async def poll_nodes(self) -> None:
        for _location in NodeLocation:
            pass

    async def build_alert_text(self, location: NodeLocation, issue: str) -> str:
        return f"Alert: {location.value} node issue detected: {issue}"
