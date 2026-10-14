"""Log failed queue jobs (Django-Q catches these before Python exception hooks)."""

import logging

from django.dispatch import receiver
from django_q.signals import post_execute_in_worker


@receiver(post_execute_in_worker, dispatch_uid="posthog_task_failure")
def capture_task_failure(sender, task, **kwargs):
    if task.get("success", True):
        return
    # Do not export task arguments, results, or arbitrary exception strings.
    function = str(task.get("func", "unknown"))[:200]
    logging.getLogger("awesome_repos.telemetry").error(
        "background_job_failed",
        extra={"task_function": function},
    )
