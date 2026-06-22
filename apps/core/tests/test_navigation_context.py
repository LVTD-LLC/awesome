from types import SimpleNamespace

from apps.core.context_processors import navigation_state


def _request_for(namespace: str, url_name: str):
    return SimpleNamespace(
        resolver_match=SimpleNamespace(namespace=namespace, url_name=url_name),
    )


def test_navigation_state_marks_repository_update_routes_active():
    for url_name in ("updates_index", "newsletter_issue_list", "newsletter_issue_detail"):
        context = navigation_state(_request_for("repos", url_name))

        assert context["nav_updates_active"] is True


def test_navigation_state_leaves_other_routes_inactive():
    context = navigation_state(_request_for("repos", "search"))

    assert context["nav_updates_active"] is False
