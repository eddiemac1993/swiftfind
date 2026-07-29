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
        var lastCartCount = -1;

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

        function marketplaceCartCount() {
            try {
                var cart = JSON.parse(window.localStorage.getItem("cart") || "{}");
                return Object.values(cart).reduce(function (total, item) {
                    var quantity = Number(item && item.quantity);
                    return total + (Number.isFinite(quantity) && quantity > 0 ? quantity : 0);
                }, 0);
            } catch (error) {
                return 0;
            }
        }

        function updateCartCount() {
            var count = marketplaceCartCount();
            if (count === lastCartCount) {
                return;
            }
            lastCartCount = count;

            document.querySelectorAll(".sf-cart-badge").forEach(function (badge) {
                badge.textContent = count > 99 ? "99+" : String(count);
                badge.hidden = count === 0;
            });

            document.querySelectorAll(".sf-cart-action").forEach(function (link) {
                link.setAttribute(
                    "aria-label",
                    "Cart, " + count + (count === 1 ? " item" : " items")
                );
            });
        }

        updateCartCount();
        window.addEventListener("storage", updateCartCount);
        window.addEventListener("swiftfind:cart-updated", updateCartCount);
        window.setInterval(updateCartCount, 1000);

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
