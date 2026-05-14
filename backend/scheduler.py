from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.container import ServiceContainer


def build_scheduler(container: ServiceContainer) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        container.monitoring.poll_nodes,
        "interval",
        minutes=1,
        id="poll-vpn-nodes",
        replace_existing=True,
    )
    scheduler.add_job(
        container.payments.reconcile_pending_payments,
        "interval",
        minutes=2,
        id="reconcile-topups",
        replace_existing=True,
    )
    scheduler.add_job(
        container.support.close_stale_tickets,
        "cron",
        hour=0,
        minute=15,
        id="close-stale-tickets",
        replace_existing=True,
    )
    return scheduler
