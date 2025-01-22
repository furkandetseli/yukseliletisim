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
import random
import string
from flask_login import login_required, current_user
from functools import wraps
from models import *
from models import User, Product, Order, OrderItem, Category, Brand, ProductImage
from extensions import db
from werkzeug.utils import secure_filename
import os
from flask_wtf.csrf import generate_csrf  # Ekleyin
from flask import jsonify  # Eğer yoksa ekleyin


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
    active_products = Product.query.filter_by(is_active=True).count()
    low_stock_count = Product.query.filter(Product.stock < 10).count()
    
    # Bu ayki yeni kullanıcılar
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = User.query.filter(User.created_at >= current_month).count()
    
    # Günlük sipariş sayısı
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_orders = Order.query.filter(Order.created_at >= today).count()
    pending_orders = Order.query.filter_by(status='Beklemede').count()
    
    # Son eklenen ürünler
    latest_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    # Son kayıt olan kullanıcılar
    latest_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Son siparişler
    latest_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         active_products=total_products,  # Geçici olarak total_products kullanıyoruz
                         low_stock_count=low_stock_count,
                         new_users_this_month=new_users_this_month,
                         daily_orders=daily_orders,
                         pending_orders=pending_orders,
                         latest_products=latest_products,
                         latest_users=latest_users,
                         latest_orders=latest_orders)

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
        try:
            # Form verilerini al
            name = request.form.get('name')
            brand_id = request.form.get('brand_id')
            category_id = request.form.get('category_id')
            price = request.form.get('price')
            stock = request.form.get('stock')
            description = request.form.get('description', '')
            
            # Validasyon
            if not name:
                flash('Ürün adı gereklidir', 'error')
                return redirect(url_for('admin.add_product'))
            if not brand_id:
                flash('Marka seçimi gereklidir', 'error')
                return redirect(url_for('admin.add_product'))
            if not price:
                flash('Fiyat gereklidir', 'error')
                return redirect(url_for('admin.add_product'))

            # Ürün oluştur
            product = Product(
                name=name,
                brand_id=int(brand_id),
                category_id=int(category_id) if category_id else None,
                price=float(price),
                stock=int(stock) if stock else 0,
                description=description,
                is_active=True
            )
            db.session.add(product)
            db.session.flush()  # ID almak için

            # Görselleri işle
            images = request.files.getlist('images')
            
            if images and any(img.filename for img in images):
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)

                for index, image in enumerate(images):
                    if image and image.filename:
                        filename = secure_filename(f"{product.id}_{index}_{image.filename}")
                        image_path = os.path.join(upload_folder, filename)
                        image.save(image_path)

                        product_image = ProductImage(
                            product_id=product.id,
                            image_path=filename,
                            is_primary=(index == 0)  # İlk görsel ana görsel
                        )
                        db.session.add(product_image)
                        db.session.add(product_image)

            db.session.commit()
            flash('Ürün başarıyla eklendi.', 'success')
            return redirect(url_for('admin.products'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ürün eklenirken bir hata oluştu: {str(e)}', 'error')
            return redirect(url_for('admin.add_product'))

    # GET request için
    brands = Brand.query.order_by(Brand.name).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/product_form.html',
                         brands=brands,
                         categories=categories)

@admin_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            name = request.form.get('name')
            brand_id = request.form.get('brand_id')
            category_id = request.form.get('category_id')
            price = request.form.get('price')
            stock = request.form.get('stock')
            description = request.form.get('description', '')
            
            # Validasyon
            errors = []
            if not name:
                errors.append("Ürün adı gerekli")
            if not brand_id:
                errors.append("Marka seçimi gerekli")
            if not category_id:
                errors.append("Kategori seçimi gerekli")
            if not price:
                errors.append("Fiyat gerekli")
            if not stock:
                errors.append("Stok adedi gerekli")
                
            # Görsel kontrolü - yeni ürünse veya mevcut görseli yoksa zorunlu
            images = request.files.getlist('images')
            has_images = any(img.filename for img in images)
            if not has_images and not product.images:
                errors.append("En az bir ürün görseli gerekli")
            
            if errors:
                flash("\n".join(errors), 'error')
                return redirect(url_for('admin.edit_product', id=id))

            # Ürün bilgilerini güncelle
            product.name = name
            product.brand_id = int(brand_id)
            product.category_id = int(category_id)
            product.price = float(price)
            product.stock = int(stock)
            product.description = description

            # Yeni görseller varsa ekle
            images = request.files.getlist('images')
            if any(img.filename for img in images):
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)

                # Yeni görselleri kaydet
                for index, image in enumerate(images):
                    if image and image.filename:
                        filename = secure_filename(f"{product.stock_code}_{len(product.images) + index}_{image.filename}")
                        image_path = os.path.join(upload_folder, filename)
                        image.save(image_path)

                        product_image = ProductImage(
                            product_id=product.id,
                            image_path=filename,
                            is_primary=(index == 0 and not product.images)  # Sadece hiç görsel yoksa ilk görsel ana görsel olsun
                        )
                        db.session.add(product_image)

            # Silinecek görseller
            deleted_images = request.form.getlist('delete_images')
            if deleted_images:
                for image_id in deleted_images:
                    image = ProductImage.query.get(int(image_id))
                    if image and image.product_id == product.id:
                        # Dosyayı sil
                        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image_path)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                        db.session.delete(image)

            db.session.commit()
            flash('Ürün başarıyla güncellendi.', 'success')
            return redirect(url_for('admin.products'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ürün güncellenirken bir hata oluştu: {str(e)}', 'error')
            return redirect(url_for('admin.edit_product', id=id))

    # GET isteği için
    brands = Brand.query.order_by(Brand.name).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/product_form.html',
                         product=product,
                         brands=brands,
                         categories=categories)


@admin_bp.route('/products/upload-image', methods=['POST'])
@login_required
@admin_required
def upload_product_image():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'Dosya bulunamadı'})
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'})
        
    if file and allowed_file(file.filename):
        try:
            # Benzersiz dosya adı oluştur
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}.{ext}"
            filename = secure_filename(unique_filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products', filename)
            
            # Dizin yoksa oluştur
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            
            image = ProductImage(
                image_path=filename,
                is_primary=False
            )
            db.session.add(image)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'image': {
                    'id': image.id,
                    'path': filename
                }
            })
        except Exception as e:
            db.session.rollback()
            # Hata durumunda dosyayı temizle
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'message': str(e)})
            
    return jsonify({'success': False, 'message': 'Desteklenmeyen dosya türü'})



@admin_bp.route('/products/delete-image/<int:image_id>', methods=['POST'])
@login_required
@admin_required
def delete_product_image(image_id):
    try:
        image = ProductImage.query.get_or_404(image_id)
        
        # Görsel dosyasını sil
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products', image.image_path)
        if os.path.exists(image_path):
            os.remove(image_path)
            
        # Eğer bu ana görsel ise ve başka görseller varsa, ilk görseli ana görsel yap
        if image.is_primary and image.product_id:
            next_image = ProductImage.query.filter_by(
                product_id=image.product_id
            ).filter(ProductImage.id != image.id).first()
            if next_image:
                next_image.is_primary = True
            
        # Veritabanından sil
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/products/set-primary-image', methods=['POST'])
@login_required
@admin_required
def set_primary_image():
    try:
        data = request.get_json()
        image_id = data.get('image_id')
        
        if not image_id:
            return jsonify({'success': False, 'message': 'Görsel ID gerekli'})
            
        image = ProductImage.query.get_or_404(image_id)
        
        # Eski ana görseli güncelle
        if image.product_id:
            old_primary = ProductImage.query.filter_by(
                product_id=image.product_id,
                is_primary=True
            ).first()
            if old_primary:
                old_primary.is_primary = False
        
        # Yeni ana görseli ayarla
        image.is_primary = True
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/products/reorder-images', methods=['POST'])
@login_required
@admin_required
def reorder_images():
    try:
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        
        if not image_ids:
            return jsonify({'success': False, 'message': 'Görsel sıralaması gerekli'})
            
        # Sıralamayı güncelle
        for index, image_id in enumerate(image_ids):
            image = ProductImage.query.get(image_id)
            if image:
                image.order = index
                
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})



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

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', None)
    
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
        
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=20)
    
    return render_template('admin/orders.html', orders=orders)

@admin_bp.route('/orders/<int:id>')
@login_required
@admin_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/<int:id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_order_status(id):
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid content type'}), 400
        
    order = Order.query.get_or_404(id)
    data = request.get_json()
    
    try:
        if not data or 'status' not in data:
            return jsonify({'success': False, 'message': 'Status not provided'}), 400
            
        order.status = data['status']
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status updated successfully',
            'new_status': order.status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.order.asc()).all()
    return render_template('admin/categories/index.html', categories=categories)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    if request.method == 'POST':
        try:
            category = Category(
                name=request.form.get('name'),
                description=request.form.get('description'),
                parent_id=request.form.get('parent_id') or None,
                is_active=bool(request.form.get('is_active')),
                order=request.form.get('order', 0),
                meta_title=request.form.get('meta_title'),
                meta_description=request.form.get('meta_description')
            )
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'categories', filename))
                    category.image = filename

            db.session.add(category)
            db.session.commit()
            flash('Kategori başarıyla oluşturuldu.', 'success')
            return redirect(url_for('admin.categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Kategori oluşturulurken bir hata oluştu: {str(e)}', 'error')
    
    parent_categories = Category.query.filter_by(parent_id=None).all()
    return render_template('admin/categories/form.html', parent_categories=parent_categories)

@admin_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            category.name = request.form.get('name')
            category.description = request.form.get('description')
            category.parent_id = request.form.get('parent_id') or None
            category.is_active = bool(request.form.get('is_active'))
            category.order = request.form.get('order', 0)
            category.meta_title = request.form.get('meta_title')
            category.meta_description = request.form.get('meta_description')
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    # Delete old image if exists
                    if category.image:
                        old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'categories', category.image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'categories', filename))
                    category.image = filename

            db.session.commit()
            flash('Kategori başarıyla güncellendi.', 'success')
            return redirect(url_for('admin.categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Kategori güncellenirken bir hata oluştu: {str(e)}', 'error')
    
    parent_categories = Category.query.filter(Category.id != id, Category.parent_id != id).all()
    return render_template('admin/categories/form.html', 
                         category=category, 
                         parent_categories=parent_categories)

@admin_bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    try:
        # Delete category image if exists
        if category.image:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'categories', category.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Update products' category to None
        for product in category.products:
            product.category_id = None
        
        # Delete category
        db.session.delete(category)
        db.session.commit()
        
        flash('Kategori başarıyla silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Kategori silinirken bir hata oluştu: {str(e)}', 'error')
    
    return redirect(url_for('admin.categories'))

@admin_bp.route('/categories/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_categories():
    try:
        categories = request.get_json()
        for category in categories:
            cat = Category.query.get(category['id'])
            if cat:
                cat.parent_id = category.get('parent_id')
                cat.order = category.get('order', 0)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/brands')
@login_required
@admin_required
def brands():
    brands = Brand.query.order_by(Brand.name).all()
    return render_template('admin/brands.html', brands=brands)

@admin_bp.route('/brands/create', methods=['POST'])
@login_required
@admin_required
def create_brand():
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'success': False, 'message': 'Marka adı gerekli'})
            
        # Marka zaten var mı kontrol et
        existing_brand = Brand.query.filter_by(name=name).first()
        if existing_brand:
            return jsonify({'success': False, 'message': 'Bu marka zaten mevcut'})
        
        # Yeni marka oluştur
        brand = Brand(name=name)
        db.session.add(brand)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Marka başarıyla eklendi'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/brands/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_brand(id):
    try:
        brand = Brand.query.get_or_404(id)
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'success': False, 'message': 'Marka adı gerekli'})
        
        # Aynı isimde başka marka var mı kontrol et
        existing_brand = Brand.query.filter(Brand.name == name, Brand.id != id).first()
        if existing_brand:
            return jsonify({'success': False, 'message': 'Bu marka adı zaten kullanılıyor'})
        
        brand.name = name
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Marka başarıyla güncellendi'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/brands/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_brand(id):
    try:
        brand = Brand.query.get_or_404(id)
        
        # Markaya ait ürün var mı kontrol et
        if brand.products:
            return jsonify({
                'success': False,
                'message': 'Bu markaya ait ürünler olduğu için silinemez'
            }), 400
        
        db.session.delete(brand)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Marka başarıyla silindi'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
