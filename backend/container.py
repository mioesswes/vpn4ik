from dataclasses import dataclass

from backend.config import Settings
from backend.user_service import UserService
from database.session import Database
from monitoring.service import MonitoringService
from payments.admin_service import AdminService
from payments.service import PaymentService
from support.service import SupportService
from xray.service import XrayService


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    database: Database
    users: UserService
    xray: XrayService
    payments: PaymentService
    support: SupportService
    monitoring: MonitoringService
    admin: AdminService
