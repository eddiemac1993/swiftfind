(function () {
    "use strict";

    if (document.documentElement.dataset.swiftfindStoreCartReady) {
        return;
    }
    document.documentElement.dataset.swiftfindStoreCartReady = "external";

    var prefix = window.location.pathname.startsWith("/swiftfind/") ? "/swiftfind" : "";
    var cartPageUrl = prefix + "/pos1/cart/";

    function readCart() {
        try {
            return JSON.parse(window.localStorage.getItem("cart") || "{}");
        } catch (error) {
            return {};
        }
    }

    function cartCount(cart) {
        return Object.values(cart).reduce(function (total, item) {
            return total + Math.max(0, Number(item.quantity) || 0);
        }, 0);
    }

    function updateStoreBadge(cart) {
        var badge = document.getElementById("cart-badge");
        if (!badge) {
            return;
        }
        var count = cartCount(cart);
        badge.textContent = count > 99 ? "99+" : String(count);
        badge.style.display = count ? "grid" : "none";
    }

    function showCartNotice(message) {
        var notice = document.createElement("div");
        notice.setAttribute("role", "status");
        notice.textContent = message;
        Object.assign(notice.style, {
            position: "fixed",
            right: "20px",
            bottom: "88px",
            zIndex: "10050",
            padding: "12px 16px",
            borderRadius: "12px",
            color: "#fff",
            background: "#172033",
            boxShadow: "0 14px 30px rgba(23,32,51,.22)",
            fontFamily: "Inter, sans-serif",
            fontWeight: "700"
        });
        document.body.appendChild(notice);
        window.setTimeout(function () {
            notice.remove();
        }, 2400);
    }

    function handleStoreClick(event) {
        var cartIcon = event.target.closest("#cart-icon");
        if (cartIcon) {
            event.preventDefault();
            window.location.href = cartPageUrl;
            return;
        }

        var button = event.target.closest(".add-to-cart-btn");
        if (!button) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();

        var card = button.closest(".product-card");
        if (!card) {
            return;
        }

        var productId = button.dataset.productId;
        var businessId = card.dataset.businessId;
        var cart = readCart();
        var existingBusinesses = new Set(
            Object.values(cart)
                .map(function (item) {
                    return String(item.businessId || "");
                })
                .filter(Boolean)
        );

        if (
            existingBusinesses.size &&
            !existingBusinesses.has(String(businessId)) &&
            !window.confirm(
                "Your cart contains products from another business. Clear it and add this product?"
            )
        ) {
            return;
        }
        if (existingBusinesses.size && !existingBusinesses.has(String(businessId))) {
            cart = {};
        }

        var priceText = card.querySelector(".product-price")?.textContent || "";
        var priceMatch = priceText.match(/ZMW\s*([\d,]+(?:\.\d+)?)/i);
        var price = priceMatch ? Number(priceMatch[1].replace(/,/g, "")) : 0;
        var productName =
            card.querySelector(".product-name")?.textContent.trim() ||
            "Marketplace product";
        var businessName =
            card.querySelector(".product-business")?.textContent.trim() ||
            document.querySelector(".store-name")?.textContent.trim() ||
            "Swiftfind business";
        var productImage = card.querySelector(".product-image img")?.src || "";

        if (cart[productId]) {
            cart[productId].quantity = (Number(cart[productId].quantity) || 0) + 1;
            cart[productId].storeUrl = window.location.pathname;
        } else {
            cart[productId] = {
                name: productName,
                price: price,
                quantity: 1,
                business: businessName,
                businessId: businessId,
                image: productImage,
                storeUrl: window.location.pathname
            };
        }

        window.localStorage.setItem("cart", JSON.stringify(cart));
        updateStoreBadge(cart);
        window.dispatchEvent(new CustomEvent("swiftfind:cart-updated"));
        showCartNotice(productName + " added to cart");
    }

    document.addEventListener("click", handleStoreClick);
    updateStoreBadge(readCart());
})();
