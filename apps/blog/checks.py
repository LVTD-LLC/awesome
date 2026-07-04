from django.core.checks import Error, register

from apps.blog.services import iter_blog_post_validation_errors


@register()
def blog_post_content_check(app_configs, **kwargs):
    if app_configs is not None and not any(
        app_config.name == "apps.blog" for app_config in app_configs
    ):
        return []

    return [
        Error(
            str(error),
            hint="Fix the markdown frontmatter in apps/blog/posts before deploying.",
            id="blog.E001",
        )
        for error in iter_blog_post_validation_errors()
    ]
