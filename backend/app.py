# app.py
from waitress import serve
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
import os
from flask_wtf.csrf import CSRFProtect
from extensions import db, login_manager, migrate, csrf
from models import * 

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Güvenli bir anahtar kullanın
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = 'your-csrf-secret-key-here'  # Güvenli bir anahtar kullanın
    
    csrf = CSRFProtect(app)
    # Yapılandırma - Upload klasörü ayarları
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'images', 'products')
    
    # Max content length ayarı
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

    db_path = os.path.join(basedir, 'database', 'database.sqlite')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id)) 

    with app.app_context():
        # Import routes
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp)
        
        # Create all tables
        db.create_all()

    # Routes
    @app.route('/')
    def index():
        # Ana sayfa route'u
        categories = Category.query.filter_by(parent_id=None).order_by(Category.order.asc()).all()
        featured_products = Product.query.order_by(db.func.random()).limit(8).all()
        new_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
        
        return render_template('index.html', 
                            categories=categories,
                            featured_products=featured_products,
                            new_products=new_products)

    @app.route('/product/<slug>')
    def product_detail(slug):
        product = Product.query.filter_by(slug=slug).first_or_404()
        related_products = []
        if product.category_id:
            related_products = Product.query.filter(
                Product.category_id == product.category_id,
                Product.id != product.id
            ).limit(4).all()
        
        return render_template('products/detail.html', 
                            product=product, 
                            related_products=related_products)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('index'))
            else:
                flash('Geçersiz email veya şifre')
                
        return render_template('auth/login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            try:
                email = request.form.get('email')
                password = request.form.get('password')
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                phone  = request.form.get('phone')

                if User.query.filter_by(email=email).first():
                    flash('Bu email adresi zaten kayıtlı')
                    return redirect(url_for('register'))
                    
                user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone
                )
                user.set_password(password)
                
                db.session.add(user)
                db.session.commit()
                
                flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Bir hata oluştu: {str(e)}')
                return redirect(url_for('register'))
                
        return render_template('auth/register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/cart')
    def cart():
        cart_items = []
        subtotal = 0
        
        if current_user.is_authenticated:
            cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
            subtotal = sum(item.product.price * item.quantity for item in cart_items)
        else:
            cart = session.get('cart', {})
            for product_id, quantity in cart.items():
                product = Product.query.get(product_id)
                if product:
                    cart_items.append({
                        'product': product,
                        'quantity': quantity
                    })
                    subtotal += product.price * quantity

        # Kargo ücreti hesaplama
        shipping_cost = 0 if subtotal >= 1000 else 29.90
        
        # Toplam tutar hesaplama
        total = subtotal + shipping_cost
        
        # Progress bar yüzdesi hesaplama
        try:
            progress_percentage = min(100, int((subtotal / 1000) * 100))
        except (ZeroDivisionError, ValueError):
            progress_percentage = 0
        
        # Bedava kargo için kalan tutar
        remaining_for_free_shipping = max(0, 1000 - subtotal)
        
        # Template'e gönderilecek veriler
        template_data = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total': total,
            'progress_percentage': progress_percentage,
            'remaining_for_free_shipping': remaining_for_free_shipping,
            'show_free_shipping_progress': subtotal < 1000,  # Progress bar'ın gösterilip gösterilmeyeceği
        }
        
        return render_template('cart.html', **template_data)


    @app.route('/cart/add/<int:product_id>', methods=['POST'])
    def add_to_cart(product_id):
        try:
            data = request.get_json()
            quantity = data.get('quantity', 1)
            
            # Ürünü veritabanından al
            product = Product.query.get_or_404(product_id)
            
            # Stok kontrolü
            if not product:
                return jsonify({
                    'success': False,
                    'message': 'Ürün bulunamadı'
                }), 404
                
            if product.stock < quantity:
                return jsonify({
                    'success': False,
                    'message': 'Yetersiz stok'
                }), 400
            
            # Kullanıcı giriş yapmışsa
            if current_user.is_authenticated:
                cart_item = CartItem.query.filter_by(
                    user_id=current_user.id,
                    product_id=product_id
                ).first()
                
                if cart_item:
                    cart_item.quantity += quantity
                else:
                    cart_item = CartItem(
                        user_id=current_user.id,
                        product_id=product_id,
                        quantity=quantity
                    )
                    db.session.add(cart_item)
                    
                db.session.commit()
                
            # Kullanıcı giriş yapmamışsa
            else:
                cart = session.get('cart', {})
                product_id_str = str(product_id)
                cart[product_id_str] = cart.get(product_id_str, 0) + quantity
                session['cart'] = cart
                session.modified = True
            
            # Sepet sayısını al
            cart_count = get_cart_count()
            
            return jsonify({
                'success': True,
                'message': 'Ürün sepete eklendi',
                'cart_count': cart_count
            })
            
        except Exception as e:
            print(f"Error in add_to_cart: {str(e)}")  # Debug için log
            return jsonify({
                'success': False,
                'message': 'Bir hata oluştu'
            }), 500

    # Helper function
    def get_cart_count():
        if current_user.is_authenticated:
            return CartItem.query.filter_by(user_id=current_user.id).count()
        return len(session.get('cart', {}))
    
    @app.route('/cart/update/<int:product_id>', methods=['POST'])
    def update_cart(product_id):
        try:
            data = request.get_json()
            quantity = int(data.get('quantity', 1))
            
            if current_user.is_authenticated:
                cart_item = CartItem.query.filter_by(
                    user_id=current_user.id,
                    product_id=product_id
                ).first_or_404()
                
                cart_item.quantity = quantity
                db.session.commit()
            else:
                cart = session.get('cart', {})
                cart[str(product_id)] = quantity
                session['cart'] = cart
                session.modified = True
            
            return jsonify({
                'success': True,
                'message': 'Sepet güncellendi'
            })
            
        except Exception as e:
            print(f"Error updating cart: {str(e)}") # Debug için log ekleyin
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @app.route('/cart/remove/<int:product_id>', methods=['POST'])
    def remove_from_cart(product_id):
        if current_user.is_authenticated:
            cart_item = CartItem.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first_or_404()
            
            db.session.delete(cart_item)
            db.session.commit()
        else:
            cart = session.get('cart', {})
            cart.pop(str(product_id), None)
            session['cart'] = cart
        
        return jsonify({'message': 'Ürün sepetten kaldırıldı'})

    @app.route('/category/<string:category_name>')
    def category_products(category_name):
        page = request.args.get('page', 1, type=int)
        sort = request.args.get('sort', 'default')
        
        # Hem ana kategori hem alt kategori kontrolü
        category = Category.query.filter_by(name=category_name).first_or_404()
        
        # Bu kategoriye ait ve alt kategorilere ait tüm ürünleri al
        query = Product.query
        
        if category.children.count() > 0:
            # Ana kategori ise, kendi ve alt kategorilerindeki ürünleri al
            subcategory_ids = [c.id for c in category.children]
            query = query.filter(
                db.or_(
                    Product.category_id == category.id,
                    Product.category_id.in_(subcategory_ids)
                )
            )
        else:
            # Alt kategori ise sadece kendi ürünlerini al
            query = query.filter_by(category_id=category.id)
        
        # Sıralama
        if sort == 'price_asc':
            query = query.order_by(Product.price.asc())
        elif sort == 'price_desc':
            query = query.order_by(Product.price.desc())
        elif sort == 'newest':
            query = query.order_by(Product.created_at.desc())
        else:
            query = query.order_by(Product.name.asc())
        
        # Sayfalama
        products = query.paginate(page=page, per_page=12)
        
        return render_template('products/category.html', 
                            products=products,
                            category=category,
                            current_sort=sort)

    @app.route('/search')
    def search():
        query = request.args.get('q', '')
        if not query:
            return redirect(url_for('index'))
            
        products = Product.query.filter(
            db.or_(
                Product.name.ilike(f'%{query}%'),
                Product.description.ilike(f'%{query}%')
            )
        ).all()
        
        return render_template('search.html', products=products, query=query)

    @app.route('/static/images/products/<path:filename>')
    def product_images(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if request.method == 'POST':
            try:
                # Kişisel bilgi güncellemesi
                current_user.first_name = request.form.get('first_name')
                current_user.last_name = request.form.get('last_name')
                current_user.email = request.form.get('email')
                phone = request.form.get('phone')
                phone = phone.replace(' ', '') if phone else None
                current_user.phone = phone
                
        
                # Şifre değişikliği kontrolü
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                
                if current_password and new_password and confirm_password:
                    if not current_user.check_password(current_password):
                        flash('Mevcut şifre hatalı', 'error')
                        return redirect(url_for('profile'))
                        
                    if new_password != confirm_password:
                        flash('Yeni şifreler eşleşmiyor', 'error')
                        return redirect(url_for('profile'))
                        
                    current_user.set_password(new_password)
                
                db.session.commit()
                flash('Bilgileriniz başarıyla güncellendi', 'success')
                return redirect(url_for('profile'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Bir hata oluştu: {str(e)}', 'error')
                return redirect(url_for('profile'))
    
        return render_template('profile.html')


    # Helper functions
    def get_cart_count():
        if current_user.is_authenticated:
            return CartItem.query.filter_by(user_id=current_user.id).count()
        else:
            return len(session.get('cart', {}))

    # Context processor
    @app.context_processor
    def utility_processor():
        def get_categories():
            return Category.query.filter_by(parent_id=None).order_by(Category.order.asc()).all()
        
        return {
            'cart_count': get_cart_count(),
            'categories': get_categories()  # Kategorileri ekledik
        }

    return app

app = create_app()

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8000) 