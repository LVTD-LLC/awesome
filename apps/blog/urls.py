from django.urls import path

from apps.blog import views

app_name = "blog"

urlpatterns = [
    path("", views.BlogPostListView.as_view(), name="post_list"),
    path("<slug:slug>/", views.BlogPostDetailView.as_view(), name="post_detail"),
]
