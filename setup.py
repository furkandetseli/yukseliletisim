import os
import sys
import json
from pathlib import Path

class ProjectSetup:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.structure = {
            'backend': {
                'templates': {
                    'includes': {
                        'header.html': self.get_header_content(),
                        'footer.html': self.get_footer_content()
                    },
                    'base.html': self.get_base_content(),
                    'index.html': self.get_index_content(),
                    'products.html': self.get_products_content(),
                    'technical_service.html': '',
                    'about.html': '',
                    'help.html': '',
                    'contact.html': '',
                    'login.html': '',
                    'account.html': '',
                    'cart.html': '',
                    'category.html': '',
                    'outlet.html': ''
                },
                'static': {
                    'css': {
                        'main.css': self.get_main_css(),
                        'header.css': '',
                        'responsive.css': ''
                    },
                    'js': {
                        'main.js': '',
                        'cart.js': '',
                        'techService.js': ''
                    },
                    'images': {}
                },
                'models': {
                    'product.py': self.get_product_model(),
                    'user.py': self.get_user_model(),
                    'service_request.py': self.get_service_model()
                },
                'database': {},
                'app.py': self.get_app_content()
            }
        }

    def create_structure(self, structure=None, parent_path=None):
        if structure is None:
            structure = self.structure
        if parent_path is None:
            parent_path = self.root_dir

        for name, content in structure.items():
            path = os.path.join(parent_path, name)
            
            # Eğer path zaten varsa, skip
            if os.path.exists(path):
                print(f"Mevcut: {path}")
                if isinstance(content, dict):
                    self.create_structure(content, path)
                continue

            if isinstance(content, dict):
                os.makedirs(path)
                print(f"Oluşturuldu: {path}")
                self.create_structure(content, path)
            else:
                # Eğer dosya içeriği varsa oluştur
                if content or content == '':
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Oluşturuldu: {path}")

    def get_app_content(self):
        return '''from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/database.sqlite'
app.config['SECRET_KEY'] = 'your-secret-key'
db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/technical-service')
def technical_service():
    return render_template('technical_service.html')

if __name__ == '__main__':
    os.makedirs('database', exist_ok=True)
    db.create_all()
    app.run(debug=True)
'''

    def get_base_content(self):
        return '''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Yüksel İletişim{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/header.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="announcement-bar">
        Türkiyenin Her Noktasına 1.000 TL ve Üzeri Tüm Siparişlerde Kargo Bedava!
    </div>
    
    {% include 'includes/header.html' %}
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    {% include 'includes/footer.html' %}
    
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>'''

    def get_header_content(self):
        return '''<header>
    <div class="top-bar">
        <div class="contact-info">
            <a href="tel:05305600735"><i class="fas fa-phone"></i> 0539 586 2718</a>
            <a href="https://wa.me/05305600735"><i class="fab fa-whatsapp"></i> 0539 586 2718</a>
            <a href="mailto:info@yukseliletisim.com"><i class="fas fa-envelope"></i> info@yukseliletisim.com</a>
        </div>
        <div class="top-menu">
            <a href="{{ url_for('about') }}">Hakkımızda</a>
            <a href="{{ url_for('help') }}">Yardım</a>
            <a href="{{ url_for('contact') }}">İletişim</a>
        </div>
    </div>
</header>'''

    def get_footer_content(self):
        return '''<footer>
    <div class="footer-content">
        <p>&copy; 2024 Yüksel İletişim. Tüm hakları saklıdır.</p>
    </div>
</footer>'''

    def get_index_content(self):
        return '''{% extends 'base.html' %}

{% block content %}
<section class="featured-products">
    <h2>Öne Çıkan Ürünler</h2>
    <div class="product-grid">
        <!-- Ürünler buraya gelecek -->
    </div>
</section>
{% endblock %}'''

    def get_products_content(self):
        return '''{% extends 'base.html' %}

{% block content %}
<div class="products-container">
    <h1>Ürünlerimiz</h1>
    <div class="product-grid">
        <!-- Ürünler buraya gelecek -->
    </div>
</div>
{% endblock %}'''

    def get_main_css(self):
        return '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
}

.announcement-bar {
    background-color: #1a237e;
    color: white;
    text-align: center;
    padding: 8px;
}'''

    def get_product_model(self):
        return '''from app import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer)'''

    def get_user_model(self):
        return '''from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))'''

    def get_service_model(self):
        return '''from app import db
from datetime import datetime

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    device_type = db.Column(db.String(50))
    problem = db.Column(db.Text)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)'''

    def setup_requirements(self):
        requirements = '''flask
flask-sqlalchemy
flask-login
werkzeug
'''
        with open('requirements.txt', 'w') as f:
            f.write(requirements)
        print("requirements.txt dosyası oluşturuldu")

def main():
    try:
        setup = ProjectSetup()
        setup.create_structure()
        setup.setup_requirements()
        print("\nProje yapısı başarıyla oluşturuldu!")
        print("\nŞimdi şu adımları izleyin:")
        print("1. pip install -r requirements.txt")
        print("2. cd backend")
        print("3. python app.py")
        print("\nTarayıcıda http://localhost:5000 adresini açın")
    except Exception as e:
        print(f"Hata oluştu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()