from backend.config import get_settings
from backend.container import ServiceContainer
from backend.user_service import UserService
from database.session import Database
from monitoring.service import MonitoringService
from payments.admin_service import AdminService
from payments.service import PaymentService
from support.service import SupportService
from xray.service import XrayService


def build_container() -> ServiceContainer:
    settings = get_settings()
    database = Database(settings.database_url)
    xray = XrayService(settings=settings)
    payments = PaymentService(settings=settings, session_factory=database.session_factory)
    users = UserService(
        settings=settings,
        session_factory=database.session_factory,
        xray=xray,
    )
    support = SupportService(settings=settings, session_factory=database.session_factory)
    monitoring = MonitoringService(settings=settings, xray=xray)
    return ServiceContainer(
        settings=settings,
        database=database,
        users=users,
        xray=xray,
        payments=payments,
        support=support,
        monitoring=monitoring,
        admin=AdminService(session_factory=database.session_factory),
    )
