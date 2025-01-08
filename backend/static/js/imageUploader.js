// Görsel yükleme işleyicisi
class ImageUploadHandler {
    constructor(options) {
        this.dropzone = document.getElementById(options.dropzoneId);
        this.previewContainer = document.getElementById(options.previewContainerId);
        this.maxFiles = options.maxFiles || 5;
        this.maxFileSize = options.maxFileSize || 2 * 1024 * 1024; // 2MB default
        this.allowedTypes = options.allowedTypes || ['image/jpeg', 'image/png', 'image/gif'];
        this.csrfToken = document.querySelector('input[name="csrf_token"]').value;
        this.currentFiles = new Set();
        this.uploadQueue = [];
        this.errors = [];
        this.sortable = null;
        
        this.init();
    }

    init() {
        this.initializeExistingImages();
        this.setupEventListeners();
        this.initializeSortable();
    }

    initializeExistingImages() {
        // Mevcut görselleri sayıya dahil et
        const existingImages = this.previewContainer.querySelectorAll('.image-item');
        existingImages.forEach(img => {
            this.currentFiles.add(img.dataset.id);
            this.setupImageActions(img);
        });
        this.updateImageCountStatus();
    }

    initializeSortable() {
        // Sortable.js ile sıralama özelliği
        this.sortable = new Sortable(this.previewContainer, {
            animation: 150,
            handle: '.image-preview', // Sadece görsel alanından tutarak sıralama
            ghostClass: 'sortable-ghost',
            onEnd: async (evt) => {
                const imageIds = Array.from(this.previewContainer.children)
                    .map(item => item.dataset.id);
                await this.updateImageOrder(imageIds);
            }
        });
    }

    setupEventListeners() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropzone.addEventListener(eventName, () => {
                this.dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropzone.addEventListener(eventName, () => {
                this.dropzone.classList.remove('dragover');
            });
        });

        this.dropzone.addEventListener('drop', (e) => {
            const files = Array.from(e.dataTransfer.files);
            this.handleFiles(files);
        });

        this.dropzone.addEventListener('click', () => {
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.multiple = true;
            fileInput.accept = this.allowedTypes.join(',');
            fileInput.style.display = 'none';
            
            fileInput.addEventListener('change', (e) => {
                const files = Array.from(e.target.files);
                this.handleFiles(files);
            });
            
            document.body.appendChild(fileInput);
            fileInput.click();
            document.body.removeChild(fileInput);
        });
    }

    async handleFiles(files) {
        this.errors = [];
        const validFiles = this.validateFiles(files);
        
        if (this.errors.length > 0) {
            this.showErrors();
            return;
        }

        // Geçerli dosyaları sıraya ekle
        validFiles.forEach(file => {
            this.uploadQueue.push(file);
        });

        // Sıradaki dosyaları yükle
        await this.processUploadQueue();
    }

    validateFiles(files) {
        const validFiles = [];

        // Toplam dosya sayısı kontrolü
        if (this.currentFiles.size + files.length > this.maxFiles) {
            this.errors.push(`En fazla ${this.maxFiles} görsel yükleyebilirsiniz`);
            return validFiles;
        }

        files.forEach(file => {
            // Dosya türü kontrolü
            if (!this.allowedTypes.includes(file.type)) {
                this.errors.push(`${file.name}: Desteklenmeyen dosya türü`);
                return;
            }

            // Dosya boyutu kontrolü
            if (file.size > this.maxFileSize) {
                this.errors.push(`${file.name}: Dosya boyutu çok büyük (max 2MB)`);
                return;
            }

            validFiles.push(file);
        });

        return validFiles;
    }

    async processUploadQueue() {
        const uploadProgress = document.createElement('div');
        uploadProgress.className = 'upload-progress';
        this.dropzone.appendChild(uploadProgress);

        try {
            for (const file of this.uploadQueue) {
                await this.uploadFile(file, uploadProgress);
            }
        } catch (error) {
            this.errors.push('Dosya yükleme sırasında bir hata oluştu');
            this.showErrors();
        } finally {
            this.uploadQueue = [];
            uploadProgress.remove();
            this.updateImageCountStatus();
        }
    }

    async uploadFile(file, progressElement) {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('csrf_token', this.csrfToken);

        try {
            progressElement.innerHTML = `
                <div class="progress">
                    <div class="progress-text">${file.name} yükleniyor...</div>
                    <div class="progress-bar"></div>
                </div>
            `;

            const response = await fetch('/admin/products/upload-image', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.currentFiles.add(data.image.id);
                this.addImagePreview(data.image);
                this.showSuccess(`${file.name} başarıyla yüklendi`);
            } else {
                throw new Error(data.message || 'Yükleme başarısız');
            }
        } catch (error) {
            this.errors.push(`${file.name}: ${error.message}`);
            this.showErrors();
        }
    }

    addImagePreview(image) {
        const div = document.createElement('div');
        div.className = 'image-item';
        div.dataset.id = image.id;
        
        div.innerHTML = `
            <div class="image-preview">
                <img src="/static/images/products/${image.path}" alt="">
                <div class="image-overlay">
                    <div class="image-actions">
                        <button type="button" class="btn-primary make-primary" ${
                            this.currentFiles.size === 1 ? 'disabled' : ''
                        }>
                            <i class="fas fa-star"></i> Ana Görsel Yap
                        </button>
                        <button type="button" class="btn-danger delete-image">
                            <i class="fas fa-trash"></i> Sil
                        </button>
                    </div>
                </div>
            </div>
            ${this.currentFiles.size === 1 ? '<div class="primary-badge">Ana Görsel</div>' : ''}
            <div class="image-order-handle">
                <i class="fas fa-grip-vertical"></i>
            </div>
        `;

        this.previewContainer.appendChild(div);
        this.setupImageActions(div);
    }

    setupImageActions(imageElement) {
        const makePrimaryBtn = imageElement.querySelector('.make-primary');
        if (makePrimaryBtn) {
            makePrimaryBtn.addEventListener('click', async () => {
                try {
                    const response = await fetch('/admin/products/set-primary-image', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.csrfToken
                        },
                        body: JSON.stringify({
                            image_id: imageElement.dataset.id
                        })
                    });

                    const data = await response.json();
                    if (data.success) {
                        this.updatePrimaryImage(imageElement);
                        this.showSuccess('Ana görsel güncellendi');
                    }
                } catch (error) {
                    this.showError('Ana görsel ayarlanırken bir hata oluştu');
                }
            });
        }

        const deleteBtn = imageElement.querySelector('.delete-image');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                if (confirm('Bu görseli silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.')) {
                    this.deleteImage(imageElement);
                }
            });
        }
    }

    async deleteImage(imageElement) {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        imageElement.appendChild(loadingOverlay);

        try {
            const response = await fetch(`/admin/products/delete-image/${imageElement.dataset.id}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });

            const data = await response.json();
            if (data.success) {
                this.currentFiles.delete(imageElement.dataset.id);
                imageElement.remove();
                this.updateImageCountStatus();
                this.showSuccess('Görsel başarıyla silindi');

                // Eğer silinen görsel ana görsel ise, ilk görseli ana görsel yap
                if (imageElement.querySelector('.primary-badge')) {
                    const firstImage = this.previewContainer.querySelector('.image-item');
                    if (firstImage) {
                        this.updatePrimaryImage(firstImage);
                    }
                }
            } else {
                throw new Error(data.message || 'Silme işlemi başarısız');
            }
        } catch (error) {
            imageElement.removeChild(loadingOverlay);
            this.showError('Görsel silinirken bir hata oluştu');
        }
    }

    async updateImageOrder(imageIds) {
        try {
            const response = await fetch('/admin/products/reorder-images', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ image_ids: imageIds })
            });

            const data = await response.json();
            if (data.success) {
                this.showSuccess('Görsel sıralaması güncellendi');
            } else {
                throw new Error(data.message || 'Sıralama güncellenemedi');
            }
        } catch (error) {
            this.showError('Sıralama güncellenirken bir hata oluştu');
        }
    }

    updatePrimaryImage(newPrimaryElement) {
        // Eski ana görseli güncelle
        const oldPrimary = this.previewContainer.querySelector('.primary-badge');
        if (oldPrimary) {
            oldPrimary.remove();
            oldPrimary.closest('.image-item').querySelector('.make-primary').disabled = false;
        }

        // Yeni ana görseli işaretle
        newPrimaryElement.querySelector('.make-primary').disabled = true;
        const primaryBadge = document.createElement('div');
        primaryBadge.className = 'primary-badge';
        primaryBadge.textContent = 'Ana Görsel';
        newPrimaryElement.appendChild(primaryBadge);
    }

    showSuccess(message) {
        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor: "#28a745",
            stopOnFocus: true
        }).showToast();
    }

    showError(message) {
        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor: "#dc3545",
            stopOnFocus: true
        }).showToast();
    }

    showErrors() {
        if (this.errors.length > 0) {
            const errorMessages = this.errors.join('\n');
            Toastify({
                text: errorMessages,
                duration: 5000,
                gravity: "top",
                position: "right",
                backgroundColor: "#dc3545",
                stopOnFocus: true,
                close: true
            }).showToast();
            this.errors = [];
        }
    }

    updateImageCountStatus() {
        const remainingSlots = this.maxFiles - this.currentFiles.size;
        const statusText = this.dropzone.querySelector('small');
        if (statusText) {
            statusText.textContent = `${remainingSlots} görsel daha ekleyebilirsiniz (max ${this.maxFiles})`;
        }
    }
}
