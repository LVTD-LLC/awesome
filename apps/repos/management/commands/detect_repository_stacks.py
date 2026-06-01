from django.core.management.base import BaseCommand

from apps.repos.models import Repository
from apps.repos.services import sync_repository_stack_detection


class Command(BaseCommand):
    help = "Detect dependency files, package managers, and stacks for indexed repositories."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of repositories to inspect.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Inspect repositories even if stack detection has already run.",
        )
        parser.add_argument(
            "--repository",
            action="append",
            default=[],
            help="Full repository name to inspect. Can be passed multiple times.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show repositories that would be inspected without calling GitHub.",
        )

    def handle(self, *args, **options):
        qs = Repository.objects.order_by("stack_detected_at", "full_name")
        repositories = options["repository"]
        if repositories:
            qs = qs.filter(full_name__in=repositories)
        elif not options["all"]:
            qs = qs.filter(stack_detected_at__isnull=True)

        limit = options["limit"]
        if limit is not None:
            qs = qs[: max(0, limit)]

        inspected = 0
        failures = 0
        for repository in qs.iterator(chunk_size=100):
            inspected += 1
            if options["dry_run"]:
                self.stdout.write(f"Would inspect {repository.full_name}")
                continue

            result = sync_repository_stack_detection(repository)
            if result.get("ok"):
                stacks = ", ".join(result.get("detected_stacks") or []) or "no stacks"
                files = len(result.get("dependency_files") or [])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Detected {stacks} from {files} dependency file(s) "
                        f"for {repository.full_name}"
                    )
                )
            else:
                failures += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to inspect {repository.full_name}: {result.get('error')}"
                    )
                )

        self.stdout.write(
            f"Inspected {inspected} repositor{'y' if inspected == 1 else 'ies'} "
            f"with {failures} failure{'s' if failures != 1 else ''}."
        )
