document.addEventListener('DOMContentLoaded', function() {
    // Element seçicileri
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    const mobileMenu = document.getElementById('mobileMenu');
    const closeMenu = document.querySelector('.close-menu');
    const searchToggle = document.getElementById('searchToggle');
    const mobileSearch = document.getElementById('mobileSearch');
    const closeSearch = document.querySelector('.close-search');
    const toggleButtons = document.querySelectorAll('.toggle-submenu');

    // Overlay oluşturma
    const overlay = document.createElement('div');
    overlay.className = 'menu-overlay';
    document.body.appendChild(overlay);

    // Menüyü açma fonksiyonu
    function openMenu() {
        mobileMenu.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    // Menüyü kapatma fonksiyonu
    function closeMenuFunc() {
        mobileMenu.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    // Event Listeners - Menü
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', openMenu);
    }

    if (closeMenu) {
        closeMenu.addEventListener('click', closeMenuFunc);
    }

    // Overlay tıklama
    overlay.addEventListener('click', closeMenuFunc);

    // Sayfa dışına tıklama kontrolü
    document.addEventListener('click', function(e) {
        if (mobileMenu && mobileMenu.classList.contains('active') && 
            !mobileMenu.contains(e.target) && 
            !mobileMenuButton.contains(e.target)) {
            closeMenuFunc();
        }
    });

    // Alt kategoriler için toggle işlevi
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const submenu = this.closest('.mobile-nav-item').querySelector('.mobile-submenu');
            if (submenu) {
                // Diğer açık menüleri kapat
                const currentlyOpen = document.querySelector('.mobile-submenu.active');
                if (currentlyOpen && currentlyOpen !== submenu) {
                    currentlyOpen.classList.remove('active');
                    const openButton = currentlyOpen.parentElement.querySelector('.toggle-submenu i');
                    if (openButton) {
                        openButton.classList.remove('fa-minus');
                        openButton.classList.add('fa-plus');
                    }
                }

                // Tıklanan menüyü aç/kapat
                submenu.classList.toggle('active');
                const icon = this.querySelector('i');
                if (icon) {
                    icon.classList.toggle('fa-plus');
                    icon.classList.toggle('fa-minus');
                }
            }
        });
    });

    // Arama fonksiyonları
    if (searchToggle && mobileSearch) {
        searchToggle.addEventListener('click', function() {
            mobileSearch.classList.add('active');
            document.body.style.overflow = 'hidden';
        });

        if (closeSearch) {
            closeSearch.addEventListener('click', function() {
                mobileSearch.classList.remove('active');
                document.body.style.overflow = '';
            });
        }
    }
});