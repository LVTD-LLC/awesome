from django.apps import AppConfig
from django.conf import settings

from awesome_repos.utils import get_awesome_repos_logger

logger = get_awesome_repos_logger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"

    def ready(self):
        import apps.core.signals  # noqa
        import apps.core.telemetry_tasks  # noqa

        if settings.POSTHOG_API_KEY:
            from awesome_repos.telemetry import configure

            configure()
