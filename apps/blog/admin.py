from django.contrib import admin

from apps.blog.models import BlogCategory, BlogPost, BlogTag


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at", "updated_at")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at", "updated_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status", "author", "published_at", "updated_at")
    search_fields = (
        "title",
        "slug",
        "excerpt",
        "content_markdown",
        "seo_title",
        "meta_description",
        "target_keyword",
    )
    list_filter = ("status", "categories", "tags", "published_at", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories", "tags")
    date_hierarchy = "published_at"
    readonly_fields = ("content_html", "created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "excerpt",
                    "content_markdown",
                    "content_html",
                    "status",
                    "author",
                    "reviewed_by",
                    "reviewed_at",
                    "published_at",
                )
            },
        ),
        ("Taxonomy", {"fields": ("categories", "tags")}),
        (
            "SEO",
            {
                "fields": (
                    "seo_title",
                    "meta_description",
                    "canonical_url",
                    "og_image_url",
                    "target_keyword",
                    "template_key",
                    "source_data",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
