document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const closeMenu = document.querySelector('.close-menu');
    const toggleButtons = document.querySelectorAll('.toggle-submenu');
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    const mobileMenu = document.getElementById('mobileMenu');
    // Overlay oluştur
    const overlay = document.createElement('div');
    overlay.className = 'menu-overlay';
    document.body.appendChild(overlay);
    // Menü açma/kapama
    mobileMenuButton.addEventListener('click', function() {
        mobileMenu.classList.add('active');
        document.body.style.overflow = 'hidden';
    });
    
    closeMenu.addEventListener('click', function() {
        mobileMenu.classList.remove('active');
        document.body.style.overflow = '';
    });
    
    // Arama açma/kapama
    searchToggle.addEventListener('click', function() {
        mobileSearch.classList.add('active');
        document.body.style.overflow = 'hidden';
    });
    
    closeSearch.addEventListener('click', function() {
        mobileSearch.classList.remove('active');
        document.body.style.overflow = '';
    });
    
    // Alt kategorileri açma/kapama
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const submenu = this.closest('.mobile-nav-item').querySelector('.mobile-submenu');
            submenu.classList.toggle('active');
            
            // İkon değiştirme
            const icon = this.querySelector('i');
            icon.classList.toggle('fa-plus');
            icon.classList.toggle('fa-minus');
        });
    });
    
    // Sayfa dışına tıklandığında menüyü kapat
    document.addEventListener('click', function(e) {
        if (mobileMenu.classList.contains('active') && 
            !mobileMenu.contains(e.target) && 
            !mobileMenuButton.contains(e.target)) {
            mobileMenu.classList.remove('active');
            document.body.style.overflow = '';
        }
    });
    menuToggle.addEventListener('click', function() {
        mobileMenu.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    });
    
    closeMenu.addEventListener('click', function() {
        mobileMenu.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    });
    
    overlay.addEventListener('click', function() {
        mobileMenu.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    });
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const submenu = this.closest('li').querySelector('ul');
            if (submenu) {
                submenu.classList.toggle('active');
                this.querySelector('i').classList.toggle('fa-plus');
                this.querySelector('i').classList.toggle('fa-minus');
            }
        });
    });
});

