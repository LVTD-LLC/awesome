from django.http import Http404
from django.shortcuts import render

from apps.blog.services import (
    BLOG_DESCRIPTION,
    BLOG_TITLE,
    BlogPostNotFound,
    BlogPostValidationError,
    blog_index_schema,
    blog_index_url,
    blog_post_schema,
    default_blog_image_url,
    get_blog_post,
    json_ld,
    list_blog_posts,
)


def post_list(request):
    posts = list_blog_posts()
    return render(
        request,
        "blog/post_list.html",
        {
            "blog_title": BLOG_TITLE,
            "blog_description": BLOG_DESCRIPTION,
            "posts": posts,
            "canonical_url": blog_index_url(),
            "og_image_url": default_blog_image_url(),
            "schema_json": json_ld(blog_index_schema(posts)),
        },
    )


def post_detail(request, slug):
    try:
        post = get_blog_post(slug)
    except (BlogPostNotFound, BlogPostValidationError) as exc:
        raise Http404("Blog post not found") from exc

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "canonical_url": post.canonical_url,
            "schema_json": json_ld(blog_post_schema(post)),
        },
    )
