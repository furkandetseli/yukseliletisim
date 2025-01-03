# models.py
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import string
from sqlalchemy.orm import validates
from slugify import slugify  # Başa ekleyin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(15))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # Yeni eklendi
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product')

# models.py'a eklenecek
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50), default='Beklemede')  # Beklemede, Onaylandı, Kargoda, Tamamlandı, İptal
    total_amount = db.Column(db.Float)
    shipping_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)  # Sipariş anındaki fiyat
    
    # İlişki
    product = db.relationship('Product')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    image = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Self-referential relationship for subcategories
    children = db.relationship(
        'Category',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<Category {self.name}>'

    def get_hierarchy(self):
        hierarchy = []
        current = self
        while current is not None:
            hierarchy.append(current)
            current = current.parent
        return list(reversed(hierarchy))

    @staticmethod
    def get_tree():
        return Category.query.filter_by(parent_id=None).all()

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# models.py içinde Brand sınıfını güncelleyelim
class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # nullable=False ekledik
    # Brand'den Product'a olan ilişki
    products = db.relationship('Product', back_populates='brand', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_code = db.Column(db.String(10), unique=True, nullable=False, name='uq_product_stock_code')
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(200), unique=True, name='uq_product_slug')
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

    def _get_description_html(self):
        if self.description:
            return self.description.replace('\n', '<br>')
        return ''
        
    description_html = property(_get_description_html)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Kategori ilişkisi
    category = db.relationship('Category', backref='products')
    # İlişkiler
    brand = db.relationship('Brand', back_populates='products')
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')

    def __init__(self, *args, **kwargs):
        if 'stock_code' not in kwargs:
            kwargs['stock_code'] = self.generate_stock_code()
        if 'slug' not in kwargs:
            kwargs['slug'] = slugify(kwargs.get('name', ''))
        super(Product, self).__init__(*args, **kwargs)

    def generate_stock_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Product.query.filter_by(stock_code=code).first():
                return code

    @validates('stock_code')
    def validate_stock_code(self, key, stock_code):
        if not stock_code:
            return self.generate_stock_code()
        return stock_code
    id = db.Column(db.Integer, primary_key=True)
    stock_code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(200), unique=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    brand = db.relationship('Brand', back_populates='products')
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')

    def __init__(self, *args, **kwargs):
        if 'stock_code' not in kwargs:
            kwargs['stock_code'] = self.generate_stock_code()
        if 'slug' not in kwargs:
            kwargs['slug'] = slugify(kwargs.get('name', ''))
        super(Product, self).__init__(*args, **kwargs)

    def generate_stock_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Product.query.filter_by(stock_code=code).first():
                return code

    @validates('stock_code')
    def validate_stock_code(self, key, stock_code):
        if not stock_code:
            return self.generate_stock_code()
        return stock_code