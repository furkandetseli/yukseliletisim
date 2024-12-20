// cart.js
document.addEventListener('DOMContentLoaded', function() {
    // Sepete Ekleme Butonu Event Listener - Bunu ekleyelim
    document.querySelectorAll('.add-to-cart-btn:not(.disabled)').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            if (!productId) {
                console.error('Product ID not found');
                return;
            }
            
            // Butonu devre dışı bırak
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Ekleniyor...';
            
            addToCart(productId)
                .then(() => {
                    // İşlem başarılı olduğunda sayfayı yenile
                    window.location.reload();
                })
                .catch(() => {
                    // Hata durumunda butonu eski haline getir
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-shopping-cart"></i> Sepete Ekle';
                });
        });
    });

 // Miktar artırma/azaltma butonları
    document.querySelectorAll('.quantity-btn').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault(); // Event yayılmasını engelleyelim
            
            const input = this.closest('.quantity-selector').querySelector('.quantity-input');
            const productId = this.closest('.cart-item').dataset.productId;
            let currentValue = parseInt(input.value);

            // Butonu devre dışı bırak
            this.disabled = true;

            try {
                // Artırma veya azaltma işlemi
                if (this.classList.contains('minus')) {
                    currentValue = Math.max(1, currentValue - 1);
                    print("-")
                } else {
                    currentValue = Math.min(99, currentValue + 1);
                    print("+")
                }

                input.value = currentValue; // Input değerini güncelle

                // Backend'e güncelleme isteği gönder
                const response = await fetch(`/cart/update/${productId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: JSON.stringify({ quantity: currentValue })
                });

                const data = await response.json();

                if (data.success) {
                    // Sepet toplamlarını güncelle
                    updateCartTotals();
                    showNotification('Sepet güncellendi', 'success');
                } else {
                    throw new Error(data.message || 'Güncelleme başarısız oldu');
                }

            } catch (error) {
                console.error('Error:', error);
                input.value = currentValue - 1; // Hata durumunda eski değere dön
                showNotification('Bir hata oluştu', 'error');
            } finally {
                // Butonu tekrar aktif et
                this.disabled = false;
            }
        });
    });

    // Input değişikliği için event listener
    document.querySelectorAll('.quantity-input').forEach(input => {
        input.addEventListener('blur', function() {  // this bağlamı için arrow function yerine normal function
            const productId = this.closest('.cart-item').dataset.productId;
            let value = parseInt(this.value);
            
            // Geçerli değer kontrolü
            if (isNaN(value) || value < 1) {
                value = 1;
            } else if (value > 99) {
                value = 99;
            }
            
            this.value = value;
            if (this.defaultValue !== value.toString()) {
                updateQuantity(productId, value);
            }
        });
    });

    // Input değişikliğini işleme fonksiyonu
    function updateFromInput() {
        const productId = this.closest('.cart-item').dataset.productId;
        let value = parseInt(this.value);
        
        // Geçerli değer kontrolü
        if (isNaN(value) || value < 1) {
            value = 1;
        } else if (value > 99) {
            value = 99;
        }
        
        this.value = value;
        if (this.defaultValue !== value.toString()) {
            updateQuantity(productId, value);
        }
    }

    // Quantity güncelleme fonksiyonunu güncelleyelim
    async function updateQuantity(productId, quantity) {
        try {
            const button = document.querySelector(`[data-product-id="${productId}"] .quantity-btn`);
            const input = document.querySelector(`[data-product-id="${productId}"] .quantity-input`);
            
            // Butonları ve input'u devre dışı bırak
            if (button) button.disabled = true;
            if (input) input.disabled = true;

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
                // Sayfayı yenilemek yerine değerleri güncelle
                const itemPrice = parseFloat(document.querySelector(`[data-product-id="${productId}"]`).dataset.price);
                const itemTotal = itemPrice * quantity;
                
                // Ürün toplamını güncelle
                const totalElement = document.querySelector(`[data-product-id="${productId}"] .item-total`);
                if (totalElement) {
                    totalElement.textContent = `${itemTotal.toFixed(2)} TL`;
                }
                
                // Sepet toplamlarını güncelle
                updateCartTotals();
                
                // Bildirim göster
                showNotification('Sepet güncellendi', 'success');
            } else {
                showNotification(data.message || 'Bir hata oluştu', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Bir hata oluştu', 'error');
        } finally {
            // Butonları ve input'u tekrar aktif et
            const button = document.querySelector(`[data-product-id="${productId}"] .quantity-btn`);
            const input = document.querySelector(`[data-product-id="${productId}"] .quantity-input`);
            
            if (button) button.disabled = false;
            if (input) input.disabled = false;
        }
    }

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