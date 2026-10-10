"""Editorial starting points backed by active catalog records, not fixed URLs."""

from apps.repos.models import AwesomeList

LIST_STARTING_POINTS = (
    (
        "awesome-selfhosted/awesome-selfhosted",
        "Run your own services",
        "Explore self-hosted applications, then check deployment needs and licenses upstream.",
    ),
    (
        "vinta/awesome-python",
        "Build with Python",
        "Find Python libraries and tools, then narrow the list to your task and stack.",
    ),
    (
        "agarrharr/awesome-cli-apps",
        "Work in the terminal",
        "Browse command-line apps, then check platform support and installation instructions.",
    ),
    (
        "public-apis/public-apis",
        "Explore API resources",
        "Browse GitHub-linked resources. The upstream list also covers APIs outside this catalog.",
    ),
)


def awesome_list_starting_points():
    lists_by_source = {
        item.repo_full_name: item
        for item in AwesomeList.objects.filter(
            repo_full_name__in=[source for source, _, _ in LIST_STARTING_POINTS],
            is_active=True,
            is_archived=False,
            is_disabled=False,
        ).only("repo_full_name", "name", "slug")
    }
    return [
        {"title": title, "description": description, "awesome_list": lists_by_source[source]}
        for source, title, description in LIST_STARTING_POINTS
        if source in lists_by_source
    ]
