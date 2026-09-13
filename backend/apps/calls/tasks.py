from celery import shared_task

from apps.calls.services.processing import process_call


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_call_task(self, call_id: str):
    process_call(call_id)
