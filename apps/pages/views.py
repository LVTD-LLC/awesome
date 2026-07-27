from allauth.account.views import SignupByPasskeyView, SignupView
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django_q.tasks import async_task

from apps.core.analytics import queue_track_event
from apps.repos.services import (
    annotate_repository_recent_growth_metrics,
    visible_repository_queryset,
)
from awesome_repos.utils import get_awesome_repos_logger

logger = get_awesome_repos_logger(__name__)


class LandingPageView(TemplateView):
    template_name = "pages/landing-page.html"
    sample_size = 4
    legacy_search_param_names = frozenset(
        {
            "q",
            "mode",
            "list",
            "language",
            "topic",
            "generated_tag",
            "framework",
            "stack",
            "package_manager",
            "has_file",
            "min_stars",
            "updated_days",
            "unmaintained_days",
            "min_age_years",
            "min_velocity_percent",
            "min_star_growth_percent",
            "min_liability_percent",
            "archived",
            "ai_development",
            "sort",
            "sort_direction",
            "page",
        }
    )

    def dispatch(self, request, *args, **kwargs):
        if self.legacy_search_param_names.intersection(request.GET):
            search_url = reverse("repos:search")
            return redirect(f"{search_url}?{request.GET.urlencode()}")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        repositories = annotate_repository_recent_growth_metrics(
            visible_repository_queryset()
        ).prefetch_related("awesome_items__awesome_list")
        context.update(
            {
                "hide_side_ad_rails": False,
                "recent_repositories": list(
                    repositories.order_by("-created_at", "full_name")[: self.sample_size]
                ),
                "most_starred_repositories": list(
                    repositories.filter(stars_growth_7d__gt=0).order_by(
                        "-stars_growth_7d",
                        "-stars",
                        "full_name",
                    )[: self.sample_size]
                ),
                "most_committed_repositories": list(
                    repositories.filter(commits_growth_7d__gt=0).order_by(
                        "-commits_growth_7d",
                        "-commit_count",
                        "full_name",
                    )[: self.sample_size]
                ),
            }
        )

        if self.request.user.is_authenticated and settings.POSTHOG_API_KEY:
            user = self.request.user
            profile = getattr(user, "profile", None)
            if profile is not None:
                async_task(
                    "apps.core.tasks.try_create_posthog_alias",
                    profile_id=profile.id,
                    cookies=self.request.COOKIES,
                    source_function="LandingPageView - get_context_data",
                    group="Create Posthog Alias",
                )

        return context


class SignupTrackingMixin:
    tracking_source_name = "signup"

    def _track_signup(self):
        user = self.user
        profile = user.profile

        async_task(
            "apps.core.tasks.try_create_posthog_alias",
            profile_id=profile.id,
            cookies=self.request.COOKIES,
            source_function=f"{self.tracking_source_name} - form_valid",
            group="Create Posthog Alias",
        )

        queue_track_event(
            profile_id=profile.id,
            event_name="signup_completed",
            properties={
                "method": self.tracking_source_name,
            },
            source_function=f"{self.tracking_source_name} - form_valid",
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        self._track_signup()
        return response


class AccountSignupView(SignupTrackingMixin, SignupView):
    # Email/password signup is disabled — GitHub OAuth is the only signup path.
    # The GET page still renders so it can show the "Sign up with GitHub" button,
    # but any POST (e.g. a hand-crafted email/password submission) is rejected.
    template_name = "account/signup.html"
    tracking_source_name = "AccountSignupView"

    def post(self, request, *args, **kwargs):
        messages.info(request, "Please sign up with GitHub.")
        return redirect("account_signup")


class AccountSignupByPasskeyView(SignupTrackingMixin, SignupByPasskeyView):
    template_name = "account/signup_by_passkey.html"
    tracking_source_name = "AccountSignupByPasskeyView"


class PrivacyPolicyView(TemplateView):
    template_name = "pages/privacy-policy.html"


class TermsOfServiceView(TemplateView):
    template_name = "pages/terms-of-service.html"
