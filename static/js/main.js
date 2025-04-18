
// ======================
// Global Variables
// ======================
let currentItem = null;
let searchTimeout;
const searchInput = document.querySelector('.search-bar input');
const productsGrid = document.querySelector('.products-grid');
const sectionHeader = document.querySelector('.products-section .section-header h3');

// Search suggestions dropdown
const searchSuggestions = document.createElement('div');
searchSuggestions.className = 'search-suggestions absolute z-50 w-full bg-white shadow-lg rounded-b-lg max-h-60 overflow-y-auto hidden';
searchSuggestions.style.top = 'calc(100% + 5px)';
searchSuggestions.style.left = '0';
document.querySelector('.search-bar').appendChild(searchSuggestions);

// Loading indicator
const loadingIndicator = document.createElement('div');
loadingIndicator.className = 'search-loading flex flex-col items-center';
loadingIndicator.innerHTML = `
    <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500 mb-2"></div>
    <span>Searching...</span>
`;
document.body.appendChild(loadingIndicator);
loadingIndicator.style.display = 'none';

// ======================
// Theme Toggle
// ======================
document.getElementById('theme-toggle').addEventListener('click', function() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    document.cookie = `darkMode=${isDark}; path=/; max-age=${60 * 60 * 24 * 365}`;
});

// ======================
// Cart Functions
// ======================
function addToCart(itemId, itemName) {
    fetch('{% url "add_to_cart" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({ item_id: itemId, quantity: 1 })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_count);
            showToast(`${itemName} added to cart!`);
        } else {
            showToast(data.message || 'Failed to add item to cart');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error adding item to cart');
    });
}

function updateCartCount(count) {
    const cartCountElements = document.querySelectorAll('.cart-count');
    cartCountElements.forEach(element => {
        element.textContent = count;
    });
}

function showToast(message) {
    const toast = document.getElementById('toast');
    document.getElementById('toast-message').textContent = message;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ======================
// Category Filtering
// ======================
function filterByCategory(categoryId) {
    window.location.href = "{% url 'home' %}?category=" + categoryId;
}

// ======================
// Modal Functions
// ======================
function openItemModal(element) {
    // Get item data from data attributes
    const item = {
        id: element.dataset.itemId,
        name: element.dataset.itemName,
        description: element.dataset.itemDescription,
        location: element.dataset.itemLocation,
        price: element.dataset.itemPrice,
        originalPrice: element.dataset.itemOriginalPrice,
        category: element.dataset.itemCategory,
        source: element.dataset.itemSource,
        image: element.dataset.itemImage
    };

    currentItem = item;
    populateModalContent(item);
    setupModalButtons(item);

    // Show modal
    document.getElementById('product-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function populateModalContent(item) {
    // Set modal content
    document.getElementById('modal-item-title').textContent = item.name;
    document.getElementById('modal-item-description').textContent = item.description;
    document.getElementById('modal-item-location').textContent = item.location;
    document.getElementById('modal-item-price').textContent = item.price;

    // Handle original price display
    const originalPriceEl = document.getElementById('modal-item-original-price');
    if (item.originalPrice) {
        originalPriceEl.textContent = item.originalPrice;
        originalPriceEl.style.display = 'inline';
    } else {
        originalPriceEl.style.display = 'none';
    }

    // Set image
    const modalImage = document.getElementById('modal-item-image');
    if (item.image) {
        modalImage.src = item.image;
        modalImage.style.display = 'block';
    } else {
        modalImage.style.display = 'none';
    }

    // Set badge
    const modalBadge = document.getElementById('modal-item-badge');
    if (document.querySelector('.product-badge')) {
        modalBadge.textContent = document.querySelector('.product-badge').textContent;
        modalBadge.style.display = 'block';
    } else {
        modalBadge.style.display = 'none';
    }

    // Set up share links
    const shareText = encodeURIComponent(`Check out this item: ${item.name}`);
    const shareUrl = encodeURIComponent(window.location.href);
    document.getElementById('modal-share-twitter').href = `https://twitter.com/intent/tweet?text=${shareText}&url=${shareUrl}`;
    document.getElementById('modal-share-facebook').href = `https://www.facebook.com/sharer/sharer.php?u=${shareUrl}`;
    document.getElementById('modal-share-whatsapp').href = `whatsapp://send?text=${shareText} - ${shareUrl}`;
}

function setupModalButtons(item) {
    document.getElementById('modal-add-to-cart-btn').onclick = function(e) {
        e.stopPropagation();
        addToCart(item.id, item.name);
    };
}

function closeModal() {
    document.getElementById('product-modal').classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Modal event listeners
document.getElementById('product-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// ======================
// Search Functions
// ======================
function performSearch(query) {
    if (query.trim() === '') {
        // If search is empty, show all items
        fetch(window.location.href.split('?')[0], {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            updateProductGrid(data.items);
            sectionHeader.textContent = 'Featured Items';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        return;
    }

    // Show loading state
    loadingIndicator.style.display = 'flex';
    productsGrid.innerHTML = '<div class="col-span-2 flex justify-center items-center py-10"><div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div></div>';

    // Scroll to search results section
    const resultsSection = document.getElementById('search-results-section');
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Fetch search results
    fetch(`?search=${encodeURIComponent(query)}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        updateProductGrid(data.items);
        sectionHeader.textContent = `Search Results for "${query}"`;

        if (data.items.length === 0) {
            showNoResultsMessage();
        }

        // Scroll again after results are loaded
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    })
    .catch(error => {
        console.error('Search error:', error);
    })
    .finally(() => {
        loadingIndicator.style.display = 'none';
    });
}

function showNoResultsMessage() {
    productsGrid.innerHTML = `
        <div class="col-span-2 text-center py-10">
            <i class="fas fa-search text-4xl text-gray-400 mb-4"></i>
            <h4 class="text-lg font-medium">No items found</h4>
            <p class="text-gray-500 mt-2">Try different keywords or browse our categories</p>
        </div>
    `;
}

function updateProductGrid(items) {
    productsGrid.innerHTML = '';

    if (items.length === 0) return;

    items.forEach(item => {
        const productCard = document.createElement('div');
        productCard.className = 'product-card';
        productCard.setAttribute('data-item-id', item.id);
        productCard.setAttribute('data-item-name', item.name);
        productCard.setAttribute('data-item-price', `K${item.price}`);
        productCard.setAttribute('data-item-location', item.location);
        productCard.setAttribute('data-item-category', item.category);
        productCard.setAttribute('data-item-image', item.image);
        productCard.onclick = function() { openItemModal(this); };

        productCard.innerHTML = `
            ${item.image ? `<img src="${item.image}" alt="${item.name}" class="product-image">` :
            `<div class="product-image bg-gray-200 flex items-center justify-center">
                <i class="fas fa-image text-gray-400 text-4xl"></i>
            </div>`}
            <div class="product-info">
                <h4 class="product-title">${item.name}</h4>
                <div class="price-container">
                    <span class="product-price">K${item.price}</span>
                </div>
                <div class="product-rating">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${item.location || 'Location not specified'}</span>
                </div>
                <button class="w-full mt-3 bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded-lg transition-colors duration-300 flex items-center justify-center"
                        onclick="event.stopPropagation(); addToCart('${item.id}', '${item.name}')">
                    <i class="fas fa-cart-plus mr-2"></i>
                    Add to Cart
                </button>
            </div>
        `;

        productsGrid.appendChild(productCard);
    });
}

// Search event listeners
searchInput.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    const query = this.value.trim();

    if (query.length > 0) {
        fetchSuggestions(query);
        searchTimeout = setTimeout(() => performSearch(query), 500);
    } else {
        searchSuggestions.classList.add('hidden');
        performSearch('');
    }
});

function fetchSuggestions(query) {
    fetch(`/search-suggestions/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.suggestions.length > 0) {
                searchSuggestions.innerHTML = data.suggestions.map(suggestion => `
                    <div class="p-3 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-0 flex items-center">
                        <i class="fas fa-search text-gray-400 mr-3"></i>
                        <div>
                            <div class="font-medium">${suggestion.text}</div>
                            <div class="text-xs text-gray-500">${suggestion.category}</div>
                        </div>
                    </div>
                `).join('');
                searchSuggestions.classList.remove('hidden');
            } else {
                searchSuggestions.classList.add('hidden');
            }
        });
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('.search-bar')) {
        searchSuggestions.classList.add('hidden');
    }
});

searchSuggestions.addEventListener('click', function(e) {
    const suggestion = e.target.closest('div[class^="p-3"]');
    if (suggestion) {
        const text = suggestion.querySelector('div > div:first-child').textContent;
        const searchTerm = text.split(' (')[0];
        searchInput.value = searchTerm;
        searchSuggestions.classList.add('hidden');
        performSearch(searchTerm);
    }
});

// ======================
// Service Worker
// ======================
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('{% static "service-worker.js" %}')
            .then(registration => {
                console.log('ServiceWorker registration successful');
            })
            .catch(err => {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}