from django.db import migrations
from django.utils import timezone

SCHEDULE_NAME = "Daily awesome-list missing repository sync"
SCHEDULE_FUNC = "apps.repos.tasks.enqueue_awesome_list_missing_repo_syncs_task"


def create_schedule(apps, schema_editor):
    Schedule = apps.get_model("django_q", "Schedule")
    Schedule.objects.update_or_create(
        name=SCHEDULE_NAME,
        defaults={
            "func": SCHEDULE_FUNC,
            "schedule_type": "D",
            "repeats": -1,
            "next_run": timezone.now(),
        },
    )


def delete_schedule(apps, schema_editor):
    Schedule = apps.get_model("django_q", "Schedule")
    Schedule.objects.filter(name=SCHEDULE_NAME, func=SCHEDULE_FUNC).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("django_q", "0019_alter_task_options_alter_ormq_key_alter_ormq_lock_and_more"),
        ("repos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_schedule, delete_schedule),
    ]
