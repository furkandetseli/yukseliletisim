// frontend/src/js/products.js
class ProductManager {
    constructor() {
        this.products = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.loading = false;
    }

    async fetchProducts(page = 1, category = null) {
        try {
            this.loading = true;
            const params = new URLSearchParams({
                page: page,
                per_page: 12
            });
            
            if (category) {
                params.append('category', category);
            }

            const response = await fetch(`/api/products?${params}`);
            const data = await response.json();
            
            this.products = data.items;
            this.currentPage = data.current_page;
            this.totalPages = data.pages;
            
            this.renderProducts();
        } catch (error) {
            console.error('Ürünler yüklenirken hata oluştu:', error);
        } finally {
            this.loading = false;
        }
    }

    renderProducts() {
        const productGrid = document.querySelector('.product-grid');
        productGrid.innerHTML = this.products.map(product => this.createProductCard(product)).join('');
        
        // Ürün kartlarına tıklama olayı ekle
        document.querySelectorAll('.product-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.add-to-cart')) {
                    const productId = card.dataset.productId;
                    window.location.href = `/urun/${productId}`;
                }
            });
        });

        // Sepete ekle butonlarına tıklama olayı ekle
        document.querySelectorAll('.add-to-cart').forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const productId = button.closest('.product-card').dataset.productId;
                this.addToCart(productId);
            });
        });
    }

    createProductCard(product) {
        return `
            <div class="product-card" data-product-id="${product.id}">
                <div class="product-image">
                    <img src="${product.image_url}" alt="${product.name}">
                    ${product.discount_percentage > 0 ? 
                        `<span class="product-badge">%${product.discount_percentage} İndirim</span>` : ''}
                </div>
                <div class="product-info">
                    <div class="product-category">${product.category}</div>
                    <h3 class="product-title">${product.name}</h3>
                    <div class="product-price">
                        ${product.old_price ? 
                            `<span class="old-price">${product.old_price.toFixed(2)} TL</span>` : ''}
                        <span class="current-price">${product.price.toFixed(2)} TL</span>
                    </div>
                    <button class="add-to-cart">
                        <i class="fas fa-shopping-cart"></i> Sepete Ekle
                    </button>
                </div>
            </div>
        `;
    }

    async addToCart(productId) {
        try {
            const response = await fetch('/api/cart/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: 1
                })
            });

            if (response.ok) {
                this.updateCartCount();
                this.showNotification('Ürün sepete eklendi');
            } else {
                throw new Error('Ürün sepete eklenemedi');
            }
        } catch (error) {
            console.error('Sepete eklerken hata oluştu:', error);
            this.showNotification('Ürün sepete eklenirken bir hata oluştu', 'error');
        }
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    async updateCartCount() {
        try {
            const response = await fetch('/api/cart/count');
            const data = await response.json();
            
            const cartCount = document.querySelector('.cart-count');
            if (cartCount) {
                cartCount.textContent = data.count;
            }
        } catch (error) {
            console.error('Sepet sayısı güncellenirken hata oluştu:', error);
        }
    }
}

// Sayfa yüklendiğinde ProductManager'ı başlat
document.addEventListener('DOMContentLoaded', () => {
    const productManager = new ProductManager();
    productManager.fetchProducts();
    
    // Kategori filtrelerini dinle
    document.querySelectorAll('.category-filter').forEach(filter => {
        filter.addEventListener('click', (e) => {
            e.preventDefault();
            const category = e.target.dataset.category;
            productManager.fetchProducts(1, category);
        });
    });
});