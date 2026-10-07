"""Capture failed queue jobs (Django-Q catches these before Python exception hooks)."""

import logging

import posthog
from django.conf import settings
from django.dispatch import receiver
from django_q.signals import post_execute_in_worker


@receiver(post_execute_in_worker, dispatch_uid="posthog_task_failure")
def capture_task_failure(sender, task, **kwargs):
    if not settings.POSTHOG_API_KEY or task.get("success", True):
        return
    # Do not export task arguments, results, or arbitrary exception strings.
    function = str(task.get("func", "unknown"))[:200]
    posthog.capture_exception(
        RuntimeError(f"Background job failed: {function}"),
        properties={"task_function": function, "task_id": str(task.get("id", ""))},
    )
    logging.getLogger("awesome_repos.telemetry").error(
        "background_job_failed",
        extra={"task_function": function},
    )
