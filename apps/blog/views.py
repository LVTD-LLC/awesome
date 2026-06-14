from django.views.generic import DetailView, ListView

from apps.blog.models import BlogPost


class BlogPostListView(ListView):
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 24

    def get_queryset(self):
        return (
            BlogPost.objects.published()
            .select_related("author")
            .prefetch_related("categories", "tags")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["blog_meta_description"] = (
            "Articles, research notes, and repository discovery guides from Awesome."
        )
        return context


class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return (
            BlogPost.objects.published()
            .select_related("author", "reviewed_by")
            .prefetch_related("categories", "tags")
        )
