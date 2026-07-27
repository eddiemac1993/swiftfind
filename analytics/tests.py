from types import SimpleNamespace

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

    def render(self, path, body=None, content_type="text/html"):
        request = self.factory.get(path)
        request.user = SimpleNamespace(is_authenticated=False)
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
        self.assertIn('class="page sf-theme"', content)
        self.assertIn("data-swiftfind-theme-bar", content)
        self.assertIn("/swiftfind/pos1/marketplace/", content)

    def test_preserves_marketplace_navigation(self):
        response = self.render(
            "/swiftfind/pos1/marketplace/",
            '<html><head></head><body class="marketplace-body">Marketplace</body></html>',
        )
        content = response.content.decode()

        self.assertIn('class="marketplace-body sf-theme"', content)
        self.assertNotIn("data-swiftfind-theme-bar", content)

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
