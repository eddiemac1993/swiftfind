(function () {
    "use strict";

    function forceLightPresentation() {
        document.documentElement.removeAttribute("data-theme");
        document.documentElement.classList.remove("dark", "dark-mode");
        if (document.body) {
            document.body.classList.remove("dark", "dark-mode");
        }

        ["theme", "darkMode", "swiftfind-theme"].forEach(function (key) {
            try {
                window.localStorage.removeItem(key);
            } catch (error) {
                // Storage can be unavailable in privacy-focused browsers.
            }
        });
    }

    function setUpNavigation() {
        var header = document.querySelector("[data-swiftfind-theme-bar]");
        var toggle = document.querySelector(".sf-menu-toggle");
        var navigation = document.getElementById("sf-primary-navigation");

        forceLightPresentation();

        document.querySelectorAll(
            "#theme-toggle, .theme-toggle, [data-theme-toggle], .bottom-nav"
        ).forEach(function (element) {
            element.setAttribute("hidden", "");
            element.setAttribute("aria-hidden", "true");
        });

        if (!header || !toggle || !navigation) {
            return;
        }

        function closeMenu() {
            header.classList.remove("sf-menu-open");
            toggle.setAttribute("aria-expanded", "false");
            toggle.setAttribute("aria-label", "Open navigation");
        }

        toggle.addEventListener("click", function () {
            var isOpen = header.classList.toggle("sf-menu-open");
            toggle.setAttribute("aria-expanded", String(isOpen));
            toggle.setAttribute(
                "aria-label",
                isOpen ? "Close navigation" : "Open navigation"
            );
        });

        navigation.addEventListener("click", function (event) {
            if (event.target.closest("a")) {
                closeMenu();
            }
        });

        document.addEventListener("click", function (event) {
            if (!header.contains(event.target)) {
                closeMenu();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                closeMenu();
                toggle.focus();
            }
        });

        window.addEventListener("resize", function () {
            if (window.innerWidth > 920) {
                closeMenu();
            }
        });
    }

    forceLightPresentation();

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setUpNavigation);
    } else {
        setUpNavigation();
    }
})();
