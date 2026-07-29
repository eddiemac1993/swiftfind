(function () {
    "use strict";

    var page = document.querySelector(".sf-cart-page");
    if (!page) {
        return;
    }

    var marketplaceUrl = page.dataset.marketplaceUrl;
    var fallbackImage = page.dataset.fallbackImage;
    var cart;
    try {
        cart = JSON.parse(window.localStorage.getItem("cart") || "{}");
    } catch (error) {
        cart = {};
    }

    var list = document.getElementById("cart-list");
    var empty = document.getElementById("cart-empty");
    var content = document.getElementById("cart-content");
    var summary = document.getElementById("cart-item-summary");
    var total = document.getElementById("cart-total");
    var checkout = document.getElementById("cart-checkout");

    function quantityCount() {
        return Object.values(cart).reduce(function (sum, item) {
            return sum + Math.max(0, Number(item.quantity) || 0);
        }, 0);
    }

    function saveAndRender() {
        window.localStorage.setItem("cart", JSON.stringify(cart));
        window.dispatchEvent(new CustomEvent("swiftfind:cart-updated"));
        render();
    }

    function actionButton(label, onClick) {
        var button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.addEventListener("click", onClick);
        return button;
    }

    function render() {
        var entries = Object.entries(cart);
        var count = quantityCount();
        var subtotal = 0;
        list.replaceChildren();
        summary.textContent = count + (count === 1 ? " item" : " items");
        empty.hidden = entries.length !== 0;
        content.hidden = entries.length === 0;

        entries.forEach(function (entry) {
            var productId = entry[0];
            var item = entry[1];
            var price = Number(item.price) || 0;
            var quantity = Math.max(1, Number(item.quantity) || 1);
            subtotal += price * quantity;

            var row = document.createElement("article");
            row.className = "sf-cart-row";

            var image = document.createElement("img");
            image.src = item.image || fallbackImage;
            image.alt = "";

            var details = document.createElement("div");
            var name = document.createElement("h2");
            name.textContent = item.name || "Marketplace product";
            var business = document.createElement("p");
            business.className = "sf-cart-row__business";
            business.textContent = item.business || "Swiftfind business";
            var priceText = document.createElement("div");
            priceText.className = "sf-cart-row__price";
            priceText.textContent = "ZMW " + price.toFixed(2);
            details.append(name, business, priceText);

            var controls = document.createElement("div");
            controls.className = "sf-cart-row__controls";
            var quantityControls = document.createElement("div");
            quantityControls.className = "sf-cart-quantity";
            var quantityOutput = document.createElement("output");
            quantityOutput.textContent = String(quantity);
            quantityControls.append(
                actionButton("−", function () {
                    if (quantity <= 1) {
                        delete cart[productId];
                    } else {
                        cart[productId].quantity = quantity - 1;
                    }
                    saveAndRender();
                }),
                quantityOutput,
                actionButton("+", function () {
                    cart[productId].quantity = quantity + 1;
                    saveAndRender();
                })
            );
            var remove = actionButton("Remove", function () {
                delete cart[productId];
                saveAndRender();
            });
            remove.className = "sf-cart-remove";
            controls.append(quantityControls, remove);
            row.append(image, details, controls);
            list.append(row);
        });

        total.textContent = "ZMW " + subtotal.toFixed(2);
        var firstItem = entries.length ? entries[0][1] : null;
        if (firstItem && firstItem.storeUrl) {
            checkout.href = firstItem.storeUrl + "?cart=open";
            checkout.textContent = "Continue to checkout";
        } else {
            checkout.href = marketplaceUrl;
            checkout.textContent = "Find this business";
        }
    }

    render();
})();
