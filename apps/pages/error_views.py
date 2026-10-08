"""Error responses must not depend on account, catalog, or sponsor queries."""

from django.http import HttpResponseNotFound
from django.template.loader import get_template


def page_not_found(request, exception):
    # Do not pass request: RequestContext runs database-backed processors even
    # for unmatched URLs. A closed connection can turn the 404 into a 500 before
    # CommonMiddleware gets a chance to append a trailing slash.
    response = HttpResponseNotFound(get_template("404.html").render({}))
    response.headers["X-Robots-Tag"] = "noindex, follow"
    return response
