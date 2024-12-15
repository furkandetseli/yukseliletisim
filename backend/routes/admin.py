# routes/admin.py
from flask import (
    Blueprint, 
    render_template, 
    redirect, 
    url_for, 
    flash, 
    request, 
    current_app
)
from flask_login import login_required, current_user
from functools import wraps
from models import User, Product
from extensions import db
from werkzeug.utils import secure_filename
import os


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Dosya yükleme için yapılandırma
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Dosya yükleme için yardımcı fonksiyon
def save_product_image(image_file):
    if image_file:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(current_app.root_path, 'static/images/products', filename)
        image_file.save(image_path)
        return filename
    return None


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bu sayfaya erişim yetkiniz yok.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # İstatistikler
    total_users = User.query.count()
    total_products = Product.query.count()
    low_stock_count = Product.query.filter(Product.stock < 10).count()
    pending_orders = 0  # Sipariş sistemi eklendiğinde güncellenecek
    
    # Son eklenen ürünler
    latest_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    # Son kayıt olan kullanıcılar
    latest_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         low_stock_count=low_stock_count,
                         pending_orders=pending_orders,
                         latest_products=latest_products,
                         latest_users=latest_users)

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=20)
    return render_template('admin/products.html', products=products)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        image = request.files.get('image')
        image_filename = save_product_image(image) if image else None
        
        product = Product(
            name=request.form.get('name'),
            category=request.form.get('category'),
            price=float(request.form.get('price')),
            stock=int(request.form.get('stock')),
            description=request.form.get('description'),
            image=image_filename
        )
        
        try:
            db.session.add(product)
            db.session.commit()
            flash('Ürün başarıyla eklendi.', 'success')
            return redirect(url_for('admin.products'))
        except Exception as e:
            db.session.rollback()
            flash('Ürün eklenirken bir hata oluştu.', 'error')
            print(f"Hata: {e}")
            
    return render_template('admin/product_form.html')

@admin_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.category = request.form.get('category')
            product.price = float(request.form.get('price'))
            product.stock = int(request.form.get('stock'))
            product.description = request.form.get('description')

            # Yeni görsel yüklendiyse
            image = request.files.get('image')
            if image and image.filename:
                # Eski görseli sil
                if product.image:
                    old_image_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, product.image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                # Yeni görseli kaydet
                image_filename = save_product_image(image)
                if image_filename:
                    product.image = image_filename

            db.session.commit()
            flash('Ürün başarıyla güncellendi.', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ürün güncellenirken bir hata oluştu: {str(e)}', 'error')
            
    return render_template('admin/product_form.html', product=product)

@admin_bp.route('/products/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    try:
        # Ürün görselini sil
        if product.image:
            image_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, product.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(product)
        db.session.commit()
        flash('Ürün başarıyla silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ürün silinirken bir hata oluştu: {str(e)}', 'error')
    
    return redirect(url_for('admin.products'))

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20)
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(id):
    user = User.query.get_or_404(id)
    if user.is_admin:
        return jsonify({'success': False, 'message': 'Admin kullanıcının durumu değiştirilemez'})
    
    data = request.get_json()
    try:
        user.is_active = data['status']
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.is_admin:
        return jsonify({'success': False, 'message': 'Admin kullanıcı silinemez'})
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Kullanıcı başarıyla silindi.', 'success')
        return redirect(url_for('admin.users'))
    except Exception as e:
        db.session.rollback()
        flash(f'Kullanıcı silinirken bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:id>/details')
@login_required
@admin_required
def user_details(id):
    user = User.query.get_or_404(id)
    
    # Kullanıcı detaylarını JSON'a çevirirken None kontrolü yapıyoruz
    data = {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name or '-',
        'last_name': user.last_name or '-',
        'phone': user.phone or '-',
        'created_at': user.created_at.strftime('%d.%m.%Y %H:%M') if user.created_at else '-',
        'last_login': user.last_login.strftime('%d.%m.%Y %H:%M') if user.last_login else 'Henüz giriş yapmadı'
    }
    
    return jsonify(data)