"""Public integration contract for mounting Swiftfind inside another Django site.

Swiftfind's reusable apps remain in this repository.  A host project imports
these constants after adding the Swiftfind repository root to ``sys.path``.
"""

SWIFTFIND_LOCAL_APPS = [
    "directory.apps.DirectoryConfig",
    "chatbot.apps.ChatbotConfig",
    "messaging.apps.MessagingConfig",
    "paper.apps.PaperConfig",
    "analytics.apps.AnalyticsConfig",
    "pos.apps.PosConfig",
    "pos_system.apps.PosSystemConfig",
    "posts.apps.PostsConfig",
    "order.apps.OrderConfig",
    "taxi.apps.TaxiConfig",
    "tracking.apps.TrackingConfig",
]

SWIFTFIND_THIRD_PARTY_APPS = [
    "webpush",
    "taggit",
    "imagekit",
    "django.contrib.humanize",
    "import_export",
    "django_admin_listfilter_dropdown",
    "rangefilter",
    "django_ckeditor_5",
    "django_user_agents",
    "django.contrib.sites",
    "phonenumber_field",
]

SWIFTFIND_INSTALLED_APPS = [
    *SWIFTFIND_LOCAL_APPS,
    *SWIFTFIND_THIRD_PARTY_APPS,
]

SWIFTFIND_MIDDLEWARE = [
    "analytics.middleware.PageVisitMiddleware",
    "django_user_agents.middleware.UserAgentMiddleware",
]

SWIFTFIND_CONTEXT_PROCESSORS = [
    "messaging.context_processors.unread_messages",
]
