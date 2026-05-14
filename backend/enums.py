from enum import StrEnum


class SubscriptionStatus(StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    BANNED = "banned"


class TicketStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class PaymentProvider(StrEnum):
    CRYPTOBOT = "cryptobot"
    YOOMONEY = "yoomoney"
    SBP = "sbp"
    PENDING_INTEGRATION = "pending_integration"


class PaymentStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    FAILED = "failed"


class NodeLocation(StrEnum):
    GERMANY = "germany"
    SWEDEN = "sweden"
    FINLAND = "finland"
    USA = "usa"


class SubscriptionPlan(StrEnum):
    MONTH_1 = "1_month"
    MONTH_3 = "3_months"
