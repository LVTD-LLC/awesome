from __future__ import annotations

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from apps.blog.markdown import render_blog_markdown
from apps.core.base_models import BaseModel


class BlogCategory(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]
        verbose_name = "Blog category"
        verbose_name_plural = "Blog categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogTag(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Blog tag"
        verbose_name_plural = "Blog tags"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(
            status=BlogPost.Status.PUBLISHED,
            published_at__isnull=False,
            published_at__lte=timezone.now(),
        )


class BlogPost(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "Review"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    excerpt = models.TextField(blank=True, default="")
    content_markdown = models.TextField(blank=True, default="")
    content_html = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="blog_posts",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_blog_posts",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    categories = models.ManyToManyField(BlogCategory, blank=True, related_name="posts")
    tags = models.ManyToManyField(BlogTag, blank=True, related_name="posts")
    seo_title = models.CharField(max_length=255, blank=True, default="")
    meta_description = models.CharField(max_length=320, blank=True, default="")
    canonical_url = models.URLField(max_length=500, blank=True, default="")
    og_image_url = models.URLField(max_length=500, blank=True, default="")
    target_keyword = models.CharField(max_length=255, blank=True, default="")
    template_key = models.CharField(max_length=120, blank=True, default="")
    source_data = models.JSONField(default=dict, blank=True)

    objects = BlogPostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["template_key"]),
            models.Index(fields=["target_keyword"]),
        ]

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        update_field_set = set(update_fields) if update_fields is not None else None
        if not self.slug:
            self.slug = slugify(self.title)
            if update_field_set is not None:
                update_field_set.add("slug")
        if update_field_set is None or "content_markdown" in update_field_set:
            self.content_html = render_blog_markdown(self.content_markdown)
            if update_field_set is not None:
                update_field_set.add("content_html")
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
            if update_field_set is not None:
                update_field_set.add("published_at")
        if update_field_set is not None:
            kwargs["update_fields"] = update_field_set
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        return (
            self.status == self.Status.PUBLISHED
            and self.published_at is not None
            and self.published_at <= timezone.now()
        )

    @property
    def display_title(self):
        return self.seo_title or self.title

    @property
    def seo_description(self):
        return self.meta_description or self.excerpt

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})
