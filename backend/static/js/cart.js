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
 // Miktar artırma/azaltma butonları
    document.querySelectorAll('.quantity-btn').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            
            if (this.disabled) return;
            
            // Gerekli elementleri bul
            const cartItem = this.closest('.cart-item');
            const input = cartItem.querySelector('.quantity-input');
            const itemTotalElement = cartItem.querySelector('.item-total');
            const productId = cartItem.dataset.productId;
            const itemPrice = parseFloat(cartItem.dataset.price);
            let currentValue = parseInt(input.value);

            console.log('Initial values:', {
                currentValue,
                itemPrice,
                currentTotal: currentValue * itemPrice
            });

            // Butonu devre dışı bırak
            this.disabled = true;

            // Artırma veya azaltma işlemi
            let newValue = currentValue;
            if (this.classList.contains('minus')) {
                newValue = Math.max(1, currentValue - 1);
            } else {
                newValue = Math.min(99, currentValue + 1);
            }

            console.log('New value:', newValue);

            // Input ve toplam değerleri güncelle
            input.value = newValue;
            const newTotal = itemPrice * newValue;
            
            // Ürün toplam fiyatını güncelle
            itemTotalElement.textContent = `${newTotal.toFixed(2)} TL`;
            
            // Genel toplamı güncelle
            updateCartTotals();

            try {
                // Backend'e gönder
                const response = await fetch(`/cart/update/${productId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: JSON.stringify({ quantity: newValue })
                });

                const data = await response.json();

                if (data.success) {
                    // Sepet toplamlarını güncelle
                    updateCartTotals();
                    showNotification('Sepet güncellendi', 'success');
                } else {
                    // Hata durumunda eski değerlere dön
                    input.value = currentValue;
                    itemTotalElement.textContent = `${(itemPrice * currentValue).toFixed(2)} TL`;
                    throw new Error(data.message || 'Güncelleme başarısız oldu');
                }

            } catch (error) {
                console.error('Error:', error);
                // Hata durumunda eski değerlere dön
                input.value = currentValue;
                itemTotalElement.textContent = `${(itemPrice * currentValue).toFixed(2)} TL`;
                showNotification('Bir hata oluştu', 'error');
            } finally {
                setTimeout(() => {
                    this.disabled = false;
                }, 300);
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
                // İlgili ürünün fiyatını ve toplam fiyatını güncelle
                const cartItem = document.querySelector(`.cart-item[data-product-id="${productId}"]`);
                if (cartItem) {
                    const itemPrice = parseFloat(cartItem.dataset.price);
                    const newTotal = itemPrice * quantity;
    
                    // Ürünün toplam fiyatını güncelle
                    const itemTotalElement = cartItem.querySelector('.item-total');
                    if (itemTotalElement) {
                        itemTotalElement.textContent = `${newTotal.toFixed(2)} TL`;
                    }
                }
                
                // Sepet toplamlarını güncelle
                updateCartTotals();
                showNotification('Sepet güncellendi', 'success');
            } else {
                throw new Error(data.message || 'Güncelleme başarısız oldu');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Bir hata oluştu', 'error');
            throw error;
        }
    }

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

    let isProcessing = false;

    // Miktar artırma/azaltma butonları - Tek bir yerde tanımlayalım
    function initializeQuantityButtons() {
        // Önce varolan event listener'ları kaldıralım
        document.querySelectorAll('.quantity-btn').forEach(btn => {
            btn.replaceWith(btn.cloneNode(true));
        });

        // Yeni event listener'ları ekleyelim
        document.querySelectorAll('.quantity-btn').forEach(btn => {
            btn.addEventListener('click', async function(e) {
                e.preventDefault();
                
                // İşlem devam ediyorsa yeni işlemi engelle
                if (isProcessing) return;
                isProcessing = true;

                const cartItem = this.closest('.cart-item');
                const input = cartItem.querySelector('.quantity-input');
                const itemTotalElement = cartItem.querySelector('.item-total');
                const productId = cartItem.dataset.productId;
                const itemPrice = parseFloat(cartItem.dataset.price);
                let currentValue = parseInt(input.value);

                try {
                    if (this.classList.contains('minus')) {
                        currentValue = Math.max(1, currentValue - 1);
                    } else {
                        currentValue = Math.min(99, currentValue + 1);
                    }

                    // Input değerini ve toplam fiyatı güncelle
                    input.value = currentValue;
                    const newTotal = itemPrice * currentValue;
                    itemTotalElement.textContent = `${newTotal.toFixed(2)} TL`;

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
                        updateCartTotals();
                        showNotification('Sepet güncellendi', 'success');
                    } else {
                        throw new Error(data.message || 'Güncelleme başarısız oldu');
                    }

                } catch (error) {
                    console.error('Error:', error);
                    input.value = currentValue - 1;
                    showNotification('Bir hata oluştu', 'error');
                } finally {
                    // İşlem bittiğinde flag'i resetle ve butonu aktif et
                    setTimeout(() => {
                        isProcessing = false;
                        this.disabled = false;
                    }, 300);
                }
            });
        });
    }

    // Sayfa yüklendiğinde butonları initialize et
    initializeQuantityButtons();

    // Mobil cihaz kontrolü
    function isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    // Sepete ekleme işlemi
    async function addToCart(productId, quantity = 1) {
        try {
            // Quantity'nin sayı olduğundan emin ol
            quantity = parseInt(quantity);
            if (isNaN(quantity) || quantity < 1) {
                quantity = 1;
            }
            
            // CSRF token'ı al
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            if (!csrfToken) {
                console.error('CSRF token bulunamadı');
                throw new Error('CSRF token bulunamadı');
            }

            // Mobil cihazlar için özel ayarlar
            const isMobile = isMobileDevice();
            const fetchOptions = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ quantity: quantity })
            };

            // Mobil cihazlarda timeout süresi
            if (isMobile) {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);
                fetchOptions.signal = controller.signal;
            }

            const response = await fetch(`/cart/add/${productId}`, fetchOptions);

            if (isMobile) {
                clearTimeout(timeoutId);
            }

            const data = await response.json();

            if (data.success) {
                updateCartCount(data.cart_count);
                
                // Mobil cihazlar için farklı bildirim
                if (isMobile) {
                    showMobileNotification('Ürün sepete eklendi', 'success');
                } else {
                    showNotification('Ürün sepete eklendi', 'success');
                }
                
                // Sepete ekle butonuna animasyon ekle
                const button = document.querySelector(`[data-product-id="${productId}"]`);
                if (button) {
                    button.classList.add('added');
                    setTimeout(() => {
                        button.classList.remove('added');
                    }, 2000);
                }

                // Mobil cihazlarda sayfa yenileme yerine sepete yönlendirme
                if (isMobile) {
                    window.location.href = '/cart';
                    return;
                }
            } else if (data.error === 'product_not_found') {
                showNotification('Ürün artık mevcut değil', 'error');
                removeFromCart(productId);
            } else {
                showNotification(data.message || 'Bir hata oluştu', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            
            // Mobil cihazlar için özel hata mesajı
            if (error.name === 'AbortError') {
                showMobileNotification('İşlem zaman aşımına uğradı, lüttekrar deneyin', 'error');
            } else {
                showNotification('Bir hata oluştu', 'error');
            }
            
            // Butonu eski haline getir
            const button = document.querySelector(`[data-product-id="${productId}"]`);
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-shopping-cart"></i> Sepete Ekle';
            }
        }
    }

    // Mobil cihazlar için bildirim sistemi
    function showMobileNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `mobile-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'times-circle'}"></i>
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
                showNotification('Ürün sepetten kaldırıldı', 'success');
                // Sayfayı yenile
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            } else {
                showNotification(data.message || 'Bir hata oluştu', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Bir hata oluştu', 'error');
            // Hata durumunda da sayfayı yenile
            setTimeout(() => {
                window.location.reload();
            }, 500);
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
    document.querySelectorAll('.cart-item').forEach(cartItem => {
        const productId = cartItem.dataset.productId;
        const price = cartItem.dataset.price;
        const itemTotal = cartItem.querySelector('.item-total');
        const quantityInput = cartItem.querySelector('.quantity-input');
        const minusBtn = cartItem.querySelector('.quantity-btn.minus');
        const plusBtn = cartItem.querySelector('.quantity-btn.plus');

        console.log('Cart Item Check:', {
            productId,
            price,
            hasItemTotal: !!itemTotal,
            itemTotalText: itemTotal ? itemTotal.textContent : null,
            hasQuantityInput: !!quantityInput,
            quantityValue: quantityInput ? quantityInput.value : null,
            hasMinusBtn: !!minusBtn,
            hasPlusBtn: !!plusBtn
        });
    });
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
    
        // Bedava kargo durumunu göster/gizle
        const freeShippingInfo = document.querySelector('.free-shipping-info');
        const shippingProgress = document.querySelector('.shipping-progress');
        
        if (subtotal >= 1000) {
            if (freeShippingInfo) freeShippingInfo.style.display = 'block';
            if (shippingProgress) shippingProgress.style.display = 'none';
        } else {
            if (freeShippingInfo) freeShippingInfo.style.display = 'none';
            if (shippingProgress) {
                shippingProgress.style.display = 'block';
                const remainingForFree = 1000 - subtotal;
                const progressText = shippingProgress.querySelector('.progress-text');
                if (progressText) {
                    progressText.textContent = `Bedava kargo için ${remainingForFree.toFixed(2)} TL daha harcayın!`;
                }
            }
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
