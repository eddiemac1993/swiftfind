"""Swiftfind routes that can be mounted below a host project's URL prefix."""

from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path, reverse_lazy
from django.views.generic.base import RedirectView

from pos_system.views import order_details
from swiftfind import seo


# This URLconf intentionally has no outer app_name.  Swiftfind predates a
# project-wide namespace and its templates/views reverse these names globally.
# Mounting it below ``/swiftfind/`` preserves those names and adds the prefix.
urlpatterns = [
    path("webpush/", include("webpush.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("directory/", include("directory.urls")),
    path("paper/", include("paper.urls")),
    path("pos/", include("pos.urls")),
    path("pos1/", include("pos_system.urls")),
    path("orders/<int:order_id>/", order_details, name="order_details_root"),
    path("posts/", include("posts.urls")),
    path("", include("order.urls")),
    path("bot/", include("chatbot.urls")),
    path("taxi/", include("taxi.urls")),
    path("tracking/", include("tracking.urls")),
    path("messages/", include("messaging.urls")),
    path("analytics/", include("analytics.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "accounts/password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "accounts/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/images/favicon.ico"),
    ),
    path("robots.txt", seo.robots, name="swiftfind-robots"),
    path("sitemap.xml", seo.sitemap, name="swiftfind-sitemap"),
    re_path(
        r"^(?P<pk>\d+)/$",
        RedirectView.as_view(pattern_name="business-detail", permanent=True),
    ),
]
