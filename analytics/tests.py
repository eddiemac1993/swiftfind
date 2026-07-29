from types import SimpleNamespace
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from swiftfind.theme import apply_swiftfind_theme


@override_settings(
    STATIC_URL="/static/",
    SWIFTFIND_ENABLED=True,
)
class SwiftfindThemeTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def render(self, path, body=None, content_type="text/html", authenticated=False):
        request = self.factory.get(path)
        request.user = SimpleNamespace(is_authenticated=authenticated)
        response = HttpResponse(
            body
            or '<html><head><title>Page</title></head><body class="page">OK</body></html>',
            content_type=content_type,
        )
        return apply_swiftfind_theme(request, response)

    def test_injects_theme_and_navigation_into_swiftfind_page(self):
        response = self.render("/swiftfind/directory/about/")
        content = response.content.decode()

        self.assertIn("swiftfind/css/modern-theme.css", content)
        self.assertIn("swiftfind/js/navigation.js", content)
        self.assertIn('class="page sf-theme"', content)
        self.assertIn("data-swiftfind-theme-bar", content)
        self.assertIn("/swiftfind/pos1/marketplace/", content)
        self.assertIn('id="sf-primary-navigation"', content)
        self.assertIn('class="sf-ai-fab"', content)
        self.assertIn('class="sf-cart-action"', content)
        self.assertIn("/swiftfind/pos1/cart/", content)
        self.assertNotIn('data-sf-nav="businesses"', content)
        self.assertNotIn('data-sf-nav="products"', content)
        self.assertNotIn(">AI Assistant</a>", content)

    @patch("swiftfind.theme._navigation_context", return_value=(7, True))
    def test_business_owner_gets_messages_orders_and_business_tools(self, _context):
        response = self.render(
            "/swiftfind/directory/profile/",
            authenticated=True,
        )
        content = response.content.decode()

        self.assertIn(">Messages</span>", content)
        self.assertIn(">Orders</a>", content)
        self.assertIn(">Business tools</a>", content)
        self.assertIn(">7</span>", content)

    @patch("swiftfind.theme._navigation_context", return_value=(0, False))
    def test_regular_user_can_add_business_from_navigation(self, _context):
        response = self.render(
            "/swiftfind/directory/profile/",
            authenticated=True,
        )

        self.assertIn(
            "/swiftfind/directory/profile/add-business/",
            response.content.decode(),
        )

    def test_replaces_marketplace_navigation_with_shared_navigation(self):
        response = self.render(
            "/swiftfind/pos1/marketplace/",
            '<html><head></head><body class="marketplace-body">Marketplace</body></html>',
        )
        content = response.content.decode()

        self.assertIn('class="marketplace-body sf-theme"', content)
        self.assertIn("data-swiftfind-theme-bar", content)
        self.assertIn('data-sf-nav="marketplace"', content)

    def test_ai_page_does_not_repeat_floating_ai_action(self):
        response = self.render("/swiftfind/pos1/ai-assistant/")

        self.assertNotIn('class="sf-ai-fab"', response.content.decode())

    def test_removes_server_rendered_dark_mode_state(self):
        response = self.render(
            "/swiftfind/directory/profile/",
            (
                '<html data-theme="dark"><head></head>'
                '<body class="profile dark-mode">Profile</body></html>'
            ),
        )
        content = response.content.decode()

        self.assertNotIn('data-theme="dark"', content)
        self.assertIn('class="profile sf-theme"', content)

    def test_does_not_theme_host_project_page(self):
        response = self.render("/")

        self.assertNotIn("data-swiftfind-theme", response.content.decode())

    def test_removes_legacy_merge_conflict_artifacts(self):
        response = self.render(
            "/swiftfind/directory/profile/products/1/delete/",
            (
                "<<<<<<< HEAD\n"
                "<html><head></head><body>Preferred</body></html>\n"
                "=======\n"
                "<html><head></head><body>Duplicate</body></html>\n"
                ">>>>>>> old-branch\n"
            ),
        )
        content = response.content.decode()

        self.assertIn("Preferred", content)
        self.assertNotIn("Duplicate", content)
        self.assertNotIn("<<<<<<<", content)
