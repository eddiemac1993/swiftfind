# Mounting Swiftfind in another Django project

Swiftfind remains a standalone Django project. Its reusable integration
surface is defined by:

- `swiftfind/integration.py` — apps, middleware and context processors.
- `swiftfind/embedded_urls.py` — routes that a host mounts below a prefix.

The host must add this repository root to `sys.path`, append the exported
settings entries, make this repository's `templates/` and `static/`
directories discoverable, and mount the routes:

```python
path("swiftfind/", include("swiftfind.embedded_urls"))
```

Do not wrap the include in an outer namespace. Existing Swiftfind templates
and views reverse their route names globally, and Django will still prepend
the `/swiftfind/` mount path.

Swiftfind's standalone entry point continues to use `swiftfind.urls`, which
adds its own admin route and then includes the same embedded routes at `/`.
