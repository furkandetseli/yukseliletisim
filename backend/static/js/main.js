document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const mobileMenu = document.getElementById('mobileMenu');
    const closeMenu = document.querySelector('.close-menu');
    const toggleButtons = document.querySelectorAll('.toggle-submenu');
    
    // Overlay oluştur
    const overlay = document.createElement('div');
    overlay.className = 'menu-overlay';
    document.body.appendChild(overlay);
    
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