"""Shared visual theme injection for Swiftfind HTML responses."""

from __future__ import annotations

import re
from html import escape

from django.conf import settings


THEME_VERSION = "2026.07.29-navigation"
_HEAD_CLOSE_RE = re.compile(r"</head\s*>", re.IGNORECASE)
_BODY_CLOSE_RE = re.compile(r"</body\s*>", re.IGNORECASE)
_BODY_OPEN_RE = re.compile(r"<body(?P<attrs>[^>]*)>", re.IGNORECASE)
_HTML_DARK_THEME_RE = re.compile(
    r"""\sdata-theme\s*=\s*(?P<quote>["'])dark(?P=quote)""",
    re.IGNORECASE,
)
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
    behavior = (
        f'<script src="{escape(static_url)}/swiftfind/js/navigation.js'
        f'?v={THEME_VERSION}" defer data-swiftfind-navigation></script>'
    )
    html, head_count = _HEAD_CLOSE_RE.subn(
        f"{stylesheet}\n{behavior}\n</head>",
        html,
        count=1,
    )
    if not head_count:
        return response

    html = _HTML_DARK_THEME_RE.sub("", html, count=1)
    html, body_count = _BODY_OPEN_RE.subn(_add_theme_body_class, html, count=1)
    if body_count:
        html = _BODY_OPEN_RE.sub(
            lambda match: f"{match.group(0)}\n{_theme_bar(request)}",
            html,
            count=1,
        )
        html = _BODY_CLOSE_RE.sub(
            f"{_ai_assistant_action(request)}\n</body>",
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
        classes = [
            class_name
            for class_name in class_match.group("value").split()
            if class_name not in {"dark", "dark-mode"}
        ]
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
    account_label = "Profile" if authenticated else "Sign in"
    unread_count = _unread_message_count(request) if authenticated else 0

    links = [
        ("Discover", f"{prefix}/", "home"),
        ("Businesses", f"{prefix}/directory/", "businesses"),
        ("Marketplace", f"{prefix}/pos1/marketplace/", "marketplace"),
        ("Products", f"{prefix}/directory/products/", "products"),
    ]
    link_parts = []
    for label, url, key in links:
        active_class = ' class="active"' if _is_active(path, url) else ""
        link_parts.append(
            f'<a href="{escape(url)}"{active_class} data-sf-nav="{key}">'
            f"{escape(label)}</a>"
        )
    link_html = "".join(link_parts)
    messages_badge = (
        f'<span class="sf-nav-badge" aria-label="{unread_count} unread messages">'
        f'{"99+" if unread_count > 99 else unread_count}</span>'
        if unread_count
        else ""
    )
    authenticated_links = (
        f'<a href="{escape(prefix)}/messages/" data-sf-nav="messages">'
        f'<span>Messages</span>{messages_badge}</a>'
        f'<a href="{escape(prefix)}/pos1/orders/" data-sf-nav="orders">Orders</a>'
        if authenticated
        else ""
    )
    session_action = (
        f'<a class="sf-menu-session" href="{escape(prefix)}/directory/logout/">Sign out</a>'
        if authenticated
        else f'<a class="sf-menu-session" href="{escape(prefix)}/directory/register/">Create account</a>'
    )
    message_aria_label = (
        f"Messages, {unread_count} unread" if unread_count else "Messages"
    )

    return (
        '<header class="sf-theme-bar" data-swiftfind-theme-bar>'
        '<div class="sf-theme-bar__inner">'
        f'<a class="sf-theme-brand" href="{escape(prefix)}/">'
        '<span class="sf-theme-brand__mark" aria-hidden="true">'
        '<svg viewBox="0 0 24 24" role="img"><path d="M13.1 2 4.8 13.1h6.1L10 22l9.2-12.5h-6.3L13.1 2Z"/></svg>'
        '</span><span class="sf-theme-brand__name">Swiftfind</span></a>'
        '<button class="sf-menu-toggle" type="button" aria-expanded="false" '
        'aria-controls="sf-primary-navigation" aria-label="Open navigation">'
        '<span></span><span></span><span></span></button>'
        f'<nav class="sf-theme-nav" id="sf-primary-navigation" '
        f'aria-label="Swiftfind navigation">{link_html}{authenticated_links}'
        '<a data-sf-nav="about" href="'
        f'{escape(prefix)}/directory/about/">About</a>'
        '<div class="sf-mobile-session">'
        f'<a href="{escape(prefix + account_path)}">{escape(account_label)}</a>'
        f"{session_action}</div></nav>"
        '<div class="sf-theme-actions">'
        f'<a class="sf-message-action" href="{escape(prefix)}/messages/" '
        f'aria-label="{escape(message_aria_label)}">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5h16v11H8l-4 3v-14Z"/></svg>'
        f"{messages_badge}</a>"
        f'<a class="sf-theme-account" href="{escape(prefix + account_path)}">'
        f"{escape(account_label)}</a></div>"
        "</div></header>"
    )


def _ai_assistant_action(request) -> str:
    path = getattr(request, "path", "/")
    prefix = "/swiftfind" if path == "/swiftfind" or path.startswith("/swiftfind/") else ""
    if "/pos1/ai-assistant/" in path:
        return ""
    return (
        f'<a class="sf-ai-fab" href="{escape(prefix)}/pos1/ai-assistant/" '
        'aria-label="Open Swiftfind AI Assistant">'
        '<svg viewBox="0 0 24 24" aria-hidden="true">'
        '<path d="m12 2 1.55 5.45L19 9l-5.45 1.55L12 16l-1.55-5.45L5 9l5.45-1.55L12 2Z"/>'
        '<path d="m18.5 15 .78 2.72L22 18.5l-2.72.78L18.5 22l-.78-2.72L15 18.5l2.72-.78L18.5 15Z"/>'
        '</svg><span>Ask Swiftfind AI</span></a>'
    )


def _unread_message_count(request) -> int:
    try:
        from messaging.context_processors import unread_messages

        return int(unread_messages(request).get("unread_count", 0))
    except Exception:
        # Navigation must never prevent a page from rendering if messaging is
        # temporarily unavailable during a migration or maintenance window.
        return 0


def _is_active(current_path: str, link_path: str) -> bool:
    if link_path.endswith("/pos1/marketplace/"):
        return "/pos1/marketplace/" in current_path
    if link_path.endswith("/directory/products/"):
        return "/directory/products/" in current_path
    if link_path.endswith("/directory/"):
        return (
            "/directory/" in current_path
            and "/directory/products/" not in current_path
            and "/directory/about/" not in current_path
        )
    return current_path.rstrip("/") == link_path.rstrip("/")
