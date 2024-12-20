// cart.js
document.addEventListener('DOMContentLoaded', function() {
    // Sepete ekleme işlemi
    async function addToCart(productId, quantity = 1) {
        try {
            const response = await fetch(`/cart/add/${productId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify({ quantity: quantity })
            });

            const data = await response.json();

            if (data.success) {
                updateCartCount(data.cart_count);
                showNotification('Ürün sepete eklendi', 'success');
                
                // Sepete ekle butonuna animasyon ekle
                const button = document.querySelector(`[data-product-id="${productId}"]`);
                if (button) {
                    button.classList.add('added');
                    setTimeout(() => {
                        button.classList.remove('added');
                    }, 2000);
                }
            } else if (data.error === 'product_not_found') {
                showNotification('Ürün artık mevcut değil', 'error');
                removeFromCart(productId);
            } else {
                showNotification(data.message || 'Bir hata oluştu', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Bir hata oluştu', 'error');
        }
    }

    // Sepetten ürün kaldırma
    async function removeFromCart(productId) {
        try {
            const response = await fetch(`/cart/remove/${productId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                }
            });

            const data = await response.json();

            if (data.success) {
                // Ürünü DOM'dan kaldır
                const cartItem = document.querySelector(`.cart-item[data-product-id="${productId}"]`);
                if (cartItem) {
                    cartItem.style.animation = 'slideOut 0.3s ease';
                    setTimeout(() => {
                        cartItem.remove();
                        updateCartTotals();
                    }, 300);
                }
                updateCartCount(data.cart_count);
                showNotification('Ürün sepetten kaldırıldı', 'success');
            } else {
                showNotification(data.message || 'Bir hata oluştu', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Bir hata oluştu', 'error');
        }
    }

    // Sepet adetini güncelleme
    async function updateQuantity(productId, quantity) {
        try {
            const response = await fetch(`/cart/update/${productId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify({ quantity: quantity })
            });

            const data = await response.json();

            if (data.success) {
                updateCartTotals();
                if (data.stock_warning) {
                    showNotification(data.stock_warning, 'warning');
                }
            } else if (data.error === 'product_not_found') {
                showNotification('Ürün artık mevcut değil', 'error');
                removeFromCart(productId);
            } else {
                showNotification(data.message || 'Bir hata oluştu', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Bir hata oluştu', 'error');
        }
    }

    // Miktar değiştirme butonları
    document.querySelectorAll('.quantity-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.closest('.quantity-selector').querySelector('.quantity-input');
            const productId = this.closest('.cart-item').dataset.productId;
            let value = parseInt(input.value);
            
            if (this.classList.contains('minus')) {
                value = Math.max(1, value - 1);
            } else {
                value = Math.min(99, value + 1);
            }
            
            input.value = value;
            updateQuantity(productId, value);
        });
    });

    // Miktar input değişikliği
    document.querySelectorAll('.quantity-input').forEach(input => {
        input.addEventListener('change', function() {
            const productId = this.closest('.cart-item').dataset.productId;
            let value = parseInt(this.value);
            
            // Geçerli değer kontrolü
            if (isNaN(value) || value < 1) {
                value = 1;
            } else if (value > 99) {
                value = 99;
            }
            
            this.value = value;
            updateQuantity(productId, value);
        });
    });

    // Sepetten kaldırma butonları
    document.querySelectorAll('.remove-item').forEach(btn => {
        btn.addEventListener('click', function() {
            const productId = this.closest('.cart-item').dataset.productId;
            removeFromCart(productId);
        });
    });

    // Sepet sayısını güncelleme
    function updateCartCount(count) {
        const cartCount = document.querySelector('.cart-count');
        if (cartCount) {
            cartCount.textContent = count;
            if (count > 0) {
                cartCount.style.display = 'flex';
            } else {
                cartCount.style.display = 'none';
            }
        }
    }

    // Sepet toplamlarını güncelleme
    function updateCartTotals() {
        const cartItems = document.querySelectorAll('.cart-item');
        let subtotal = 0;
        
        cartItems.forEach(item => {
            const price = parseFloat(item.dataset.price);
            const quantity = parseInt(item.querySelector('.quantity-input').value);
            subtotal += price * quantity;
        });

        // KDV ve kargo hesaplama
        const shipping = subtotal >= 1000 ? 0 : 29.90;
        const total = subtotal + shipping;

        // Toplamları güncelle
        document.querySelector('.subtotal-amount').textContent = `${subtotal.toFixed(2)} TL`;
        document.querySelector('.shipping-amount').textContent = shipping === 0 ? 'Ücretsiz' : `${shipping.toFixed(2)} TL`;
        document.querySelector('.total-amount').textContent = `${total.toFixed(2)} TL`;

        // Sepet boşsa mesaj göster
        const emptyCart = document.querySelector('.empty-cart');
        const cartContent = document.querySelector('.cart-content');
        
        if (cartItems.length === 0) {
            if (emptyCart) emptyCart.style.display = 'block';
            if (cartContent) cartContent.style.display = 'none';
        } else {
            if (emptyCart) emptyCart.style.display = 'none';
            if (cartContent) cartContent.style.display = 'block';
        }
    }

    // Bildirim gösterme
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'times-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animasyon ekle
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Bildirimi kaldır
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // İlk yüklemede toplamları güncelle
    updateCartTotals();
});