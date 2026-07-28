from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from directory.models import Business


class SwiftfindSEOTests(TestCase):
    def setUp(self):
        notification_patch = patch(
            "directory.signals.send_business_creation_notification"
        )
        welcome_patch = patch("directory.signals.send_business_welcome_email")
        notification_patch.start()
        welcome_patch.start()
        self.addCleanup(notification_patch.stop)
        self.addCleanup(welcome_patch.stop)
        owner = get_user_model().objects.create_user(
            username="seo-test-owner",
            email="owner@example.com",
        )
        self.business = Business.objects.create(
            name="Searchable Zambian Company",
            description="A company that should be discoverable in search.",
            address="Lusaka",
            phone_number="0970000000",
            city="Lusaka",
            status="active",
            owner=owner,
        )

    def test_sitemap_contains_active_business_canonical_url(self):
        response = self.client.get(reverse("swiftfind-sitemap"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertContains(
            response,
            self.business.get_absolute_url(),
        )

    def test_robots_advertises_current_sitemap(self):
        response = self.client.get(reverse("swiftfind-robots"))

        self.assertContains(response, reverse("swiftfind-sitemap"))
        self.assertNotContains(response, "swiftfindzm.com")

    def test_legacy_business_url_redirects_to_canonical_url(self):
        response = self.client.get(
            reverse("legacy-business-detail", kwargs={"pk": self.business.pk})
        )

        self.assertRedirects(
            response,
            self.business.get_absolute_url(),
            status_code=301,
            fetch_redirect_response=False,
        )
