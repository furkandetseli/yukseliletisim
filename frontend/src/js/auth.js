// frontend/src/js/auth.js
class AuthManager {
    constructor() {
        this.initializeForm();
    }

    initializeForm() {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');

        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
            this.initializePasswordValidation();
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: formData.get('email'),
                    password: formData.get('password')
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Başarılı giriş
                this.showMessage('Giriş başarılı, yönlendiriliyorsunuz...', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                // Hata mesajı göster
                this.showMessage(data.error, 'error');
            }
        } catch (error) {
            this.showMessage('Bir hata oluştu. Lütfen tekrar deneyin.', 'error');
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const formData = new FormData(e.target);

        if (formData.get('password') !== formData.get('password_confirm')) {
            this.showMessage('Şifreler eşleşmiyor', 'error');
            return;
        }

        if (!this.validatePassword(formData.get('password'))) {
            this.showMessage('Şifre en az 8 karakter uzunluğunda olmalı ve en az bir büyük harf, bir küçük harf ve bir rakam içermelidir.', 'error');
            return;
        }

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: formData.get('email'),
                    password: formData.get('password'),
                    first_name: formData.get('first_name'),
                    last_name: formData.get('last_name'),
                    phone: formData.get('phone')
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage('Kayıt başarılı! Giriş sayfasına yönlendiriliyorsunuz...', 'success');
                setTimeout(() => {
                    window.location.href = '/giris-yap';
                }, 2000);
            } else {
                this.showMessage(data.error, 'error');
            }
        } catch (error) {
            this.showMessage('Bir hata oluştu. Lütfen tekrar deneyin.', 'error');
        }
    }

    validatePassword(password) {
        // En az 8 karakter, bir büyük harf, bir küçük harf ve bir rakam
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/;
        return passwordRegex.test(password);
    }

    initializePasswordValidation() {
        const passwordInput = document.getElementById('password');
        const passwordConfirmInput = document.getElementById('passwordConfirm');
        
        if (passwordInput && passwordConfirmInput) {
            passwordConfirmInput.addEventListener('input', () => {
                if (passwordInput.value !== passwordConfirmInput.value) {
                    passwordConfirmInput.setCustomValidity('Şifreler eşleşmiyor');
                } else {
                    passwordConfirmInput.setCustomValidity('');
                }
            });

            passwordInput.addEventListener('input', () => {
                if (!this.validatePassword(passwordInput.value)) {
                    passwordInput.setCustomValidity('Şifre kriterlere uygun değil');
                } else {
                    passwordInput.setCustomValidity('');
                    if (passwordConfirmInput.value) {
                        passwordConfirmInput.dispatchEvent(new Event('input'));
                    }
                }
            });
        }
    }

    async handleResetPassword(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            const response = await fetch('/api/auth/reset-password-request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: formData.get('email')
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage('Şifre sıfırlama talimatları email adresinize gönderildi.', 'success');
            } else {
                this.showMessage(data.error, 'error');
            }
        } catch (error) {
            this.showMessage('Bir hata oluştu. Lütfen tekrar deneyin.', 'error');
        }
    }

    showMessage(message, type) {
        const existingMessage = document.querySelector('.message');
        if (existingMessage) {
            existingMessage.remove();
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}-message`;
        messageElement.textContent = message;

        const form = document.querySelector('.auth-form');
        form.insertBefore(messageElement, form.firstChild);

        // 5 saniye sonra mesajı kaldır
        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }

    // Form input validasyonlarını kontrol et
    validateForm(formElement) {
        const inputs = formElement.querySelectorAll('input[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                this.showInputError(input, 'Bu alan zorunludur');
                isValid = false;
            } else {
                this.clearInputError(input);
            }
        });

        return isValid;
    }

    showInputError(input, message) {
        const formGroup = input.closest('.form-group');
        formGroup.classList.add('error');
        
        const existingError = formGroup.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        formGroup.appendChild(errorElement);
    }

    clearInputError(input) {
        const formGroup = input.closest('.form-group');
        formGroup.classList.remove('error');
        
        const existingError = formGroup.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
    }
}

// Sayfa yüklendiğinde AuthManager'ı başlat
document.addEventListener('DOMContentLoaded', () => {
    new AuthManager();
});