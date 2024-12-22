# backend/routes/product_routes.py
from flask import Blueprint, jsonify, request
from models.product import Product
from app import db

product_bp = Blueprint('product', __name__)

@product_bp.route('/api/products', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    category = request.args.get('category')
    
    query = Product.query
    
    if category:
        query = query.filter_by(category=category)
    
    products = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [{
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'old_price': p.old_price,
            'description': p.description,
            'category': p.category,
            'image_url': p.image_url,
            'stock': p.stock,
            'discount_percentage': p.discount_percentage
        } for p in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': products.page
    })

@product_bp.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'old_price': product.old_price,
        'description': product.description,
        'category': product.category,
        'image_url': product.image_url,
        'stock': product.stock,
        'discount_percentage': product.discount_percentage
    })

# backend/models/product.py (güncelleme)
from app import db
from datetime import datetime

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(200))
    stock = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def discount_percentage(self):
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0