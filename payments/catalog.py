from dataclasses import dataclass

from backend.enums import SubscriptionPlan


@dataclass(frozen=True, slots=True)
class PlanDefinition:
    plan: SubscriptionPlan
    months: int
    amount_rub: int
    title: str


PLANS = {
    SubscriptionPlan.MONTH_1: PlanDefinition(
        plan=SubscriptionPlan.MONTH_1,
        months=1,
        amount_rub=150,
        title="1 месяц",
    ),
    SubscriptionPlan.MONTH_3: PlanDefinition(
        plan=SubscriptionPlan.MONTH_3,
        months=3,
        amount_rub=400,
        title="3 месяца",
    ),
}
