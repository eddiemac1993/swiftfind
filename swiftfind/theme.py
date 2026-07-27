"""Shared visual theme injection for Swiftfind HTML responses."""

from __future__ import annotations

import re
from html import escape

from django.conf import settings


THEME_VERSION = "2026.07.27"
_HEAD_CLOSE_RE = re.compile(r"</head\s*>", re.IGNORECASE)
_BODY_OPEN_RE = re.compile(r"<body(?P<attrs>[^>]*)>", re.IGNORECASE)
_CLASS_RE = re.compile(
    r"""class\s*=\s*(?P<quote>["'])(?P<value>.*?)(?P=quote)""",
    re.IGNORECASE | re.DOTALL,
)
_COMMITTED_CONFLICT_RE = re.compile(
    r"^<<<<<<< HEAD\r?\n(?P<head>.*?)^=======\r?\n.*?^>>>>>>>[^\r\n]*\r?\n?",
    re.MULTILINE | re.DOTALL,
)


def apply_swiftfind_theme(request, response):
    """Add the shared Swiftfind theme to eligible HTML responses.

    Swiftfind runs both as a standalone Django project and below
    ``/swiftfind/`` in Dream Bolt. The path check keeps host-project pages
    untouched while giving both Swiftfind modes the same presentation.
    """

    if not _is_themeable_response(request, response):
        return response

    try:
        html = response.content.decode(response.charset or "utf-8")
    except (AttributeError, UnicodeDecodeError):
        return response

    # Two legacy templates were committed with visible merge-conflict
    # artifacts. Prefer their HEAD section so users never receive duplicated
    # documents or marker text while those templates remain backwards
    # compatible with the standalone project.
    html = _COMMITTED_CONFLICT_RE.sub(lambda match: match.group("head"), html)

    if "data-swiftfind-theme" in html:
        return response

    static_url = str(getattr(settings, "STATIC_URL", "/static/")).rstrip("/")
    stylesheet = (
        f'<link rel="stylesheet" '
        f'href="{escape(static_url)}/swiftfind/css/modern-theme.css'
        f'?v={THEME_VERSION}" data-swiftfind-theme="{THEME_VERSION}">'
    )
    html, head_count = _HEAD_CLOSE_RE.subn(
        f"{stylesheet}\n</head>",
        html,
        count=1,
    )
    if not head_count:
        return response

    html, body_count = _BODY_OPEN_RE.subn(_add_theme_body_class, html, count=1)
    if body_count and "marketplace-body" not in html:
        html = _BODY_OPEN_RE.sub(
            lambda match: f"{match.group(0)}\n{_theme_bar(request)}",
            html,
            count=1,
        )

    response.content = html.encode(response.charset or "utf-8")
    response["Content-Length"] = str(len(response.content))
    return response


def _is_themeable_response(request, response) -> bool:
    if getattr(response, "streaming", False):
        return False
    if getattr(response, "status_code", 500) >= 500:
        return False
    if "text/html" not in response.get("Content-Type", "").lower():
        return False

    path = getattr(request, "path", "/")
    if path.startswith(("/static/", "/media/", "/admin/")):
        return False

    # When mounted in Dream Bolt, only style the Swiftfind URL space.
    if getattr(settings, "SWIFTFIND_ENABLED", False):
        return path == "/swiftfind" or path.startswith("/swiftfind/")
    return True


def _add_theme_body_class(match: re.Match[str]) -> str:
    attrs = match.group("attrs") or ""
    class_match = _CLASS_RE.search(attrs)
    if class_match:
        classes = class_match.group("value").split()
        if "sf-theme" not in classes:
            classes.append("sf-theme")
        replacement = (
            f'class={class_match.group("quote")}'
            f'{" ".join(classes)}{class_match.group("quote")}'
        )
        attrs = (
            attrs[: class_match.start()]
            + replacement
            + attrs[class_match.end() :]
        )
    else:
        attrs = f'{attrs} class="sf-theme"'
    return f"<body{attrs}>"


def _theme_bar(request) -> str:
    path = getattr(request, "path", "/")
    prefix = "/swiftfind" if path == "/swiftfind" or path.startswith("/swiftfind/") else ""
    user = getattr(request, "user", None)
    authenticated = bool(user and getattr(user, "is_authenticated", False))
    account_path = "/directory/profile/" if authenticated else "/accounts/login/"
    account_label = "My account" if authenticated else "Sign in"

    links = [
        ("Discover", f"{prefix}/"),
        ("Marketplace", f"{prefix}/pos1/marketplace/"),
        ("Businesses", f"{prefix}/directory/"),
        ("About", f"{prefix}/directory/about/"),
        ("AI Assistant", f"{prefix}/pos1/ai-assistant/"),
    ]
    link_parts = []
    for label, url in links:
        active_class = ' class="active"' if _is_active(path, url) else ""
        link_parts.append(
            f'<a href="{escape(url)}"{active_class}>{escape(label)}</a>'
        )
    link_html = "".join(link_parts)

    return (
        '<header class="sf-theme-bar" data-swiftfind-theme-bar>'
        '<div class="sf-theme-bar__inner">'
        f'<a class="sf-theme-brand" href="{escape(prefix)}/">'
        '<span class="sf-theme-brand__mark" aria-hidden="true">⚡</span>'
        '<span>Swiftfind</span></a>'
        f'<nav class="sf-theme-nav" aria-label="Swiftfind navigation">{link_html}</nav>'
        f'<a class="sf-theme-account" href="{escape(prefix + account_path)}">'
        f"{escape(account_label)}</a>"
        "</div></header>"
    )


def _is_active(current_path: str, link_path: str) -> bool:
    if link_path.endswith("/pos1/marketplace/"):
        return "/pos1/marketplace/" in current_path
    if link_path.endswith("/directory/about/"):
        return "/directory/about/" in current_path
    if link_path.endswith("/pos1/ai-assistant/"):
        return "/pos1/ai-assistant/" in current_path
    if link_path.endswith("/directory/"):
        return "/directory/" in current_path and "/directory/about/" not in current_path
    return current_path.rstrip("/") == link_path.rstrip("/")
