"""Search-engine discovery endpoints for Swiftfind."""

from xml.etree.ElementTree import Element, SubElement, tostring

from django.http import HttpResponse
from django.urls import reverse

from directory.models import Business


PUBLIC_STATIC_ROUTES = (
    ("discover", "daily", "1.0"),
    ("business-list", "daily", "0.9"),
    ("about", "monthly", "0.6"),
    ("contact", "monthly", "0.5"),
)


def sitemap(request):
    """Return canonical public Swiftfind URLs, including every active company."""

    root = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    for route_name, change_frequency, priority in PUBLIC_STATIC_ROUTES:
        _add_url(
            root,
            request.build_absolute_uri(reverse(route_name)),
            change_frequency,
            priority,
        )

    businesses = (
        Business.objects.filter(status="active")
        .only("pk", "updated_at")
        .order_by("pk")
    )
    for business in businesses.iterator():
        _add_url(
            root,
            request.build_absolute_uri(business.get_absolute_url()),
            "weekly",
            "0.8",
            business.updated_at.date().isoformat(),
        )

    xml = b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(
        root, encoding="utf-8"
    )
    return HttpResponse(xml, content_type="application/xml")


def robots(request):
    """Advertise the current embedded sitemap and keep private areas unindexed."""

    sitemap_url = request.build_absolute_uri(reverse("swiftfind-sitemap"))
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /swiftfind/",
            "Disallow: /swiftfind/admin/",
            "Disallow: /swiftfind/accounts/",
            "Disallow: /swiftfind/directory/profile/",
            "Disallow: /swiftfind/messages/",
            "",
            f"Sitemap: {sitemap_url}",
            "",
        ]
    )
    return HttpResponse(content, content_type="text/plain")


def _add_url(root, location, change_frequency, priority, last_modified=None):
    node = SubElement(root, "url")
    SubElement(node, "loc").text = location
    if last_modified:
        SubElement(node, "lastmod").text = last_modified
    SubElement(node, "changefreq").text = change_frequency
    SubElement(node, "priority").text = priority
