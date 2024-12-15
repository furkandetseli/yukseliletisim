# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
import os

from extensions import db, login_manager, migrate, csrf
from models import User, Product, CartItem

def create_app():
    app = Flask(__name__)
    
    # Yapılandırma
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'database', 'database.sqlite')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images', 'products')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'login'

    @login_manager.user_loader 
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        # Import routes
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp)
        
        # Create all tables
        db.create_all()

    # Routes
    @app.route('/')
    def index():
        products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
        return render_template('index.html', products=products)

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
                
                if User.query.filter_by(email=email).first():
                    flash('Bu email adresi zaten kayıtlı')
                    return redirect(url_for('register'))
                    
                user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name
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
        total = 0
        
        if current_user.is_authenticated:
            cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
            total = sum(item.product.price * item.quantity for item in cart_items)
        else:
            cart = session.get('cart', {})
            for product_id, quantity in cart.items():
                product = Product.query.get(product_id)
                if product:
                    cart_items.append({
                        'product': product,
                        'quantity': quantity
                    })
                    total += product.price * quantity
        
        return render_template('cart/cart.html', 
                             cart_items=cart_items,
                             total=total)

    @app.route('/cart/add/<int:product_id>', methods=['POST'])
    def add_to_cart(product_id):
        product = Product.query.get_or_404(product_id)
        quantity = int(request.form.get('quantity', 1))
        
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
        else:
            cart = session.get('cart', {})
            cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
            session['cart'] = cart
        
        return jsonify({
            'message': 'Ürün sepete eklendi',
            'cart_count': get_cart_count()
        })

    @app.route('/cart/update/<int:product_id>', methods=['POST'])
    def update_cart(product_id):
        quantity = int(request.form.get('quantity', 1))
        
        if current_user.is_authenticated:
            cart_item = CartItem.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first_or_404()
            
            if quantity > 0:
                cart_item.quantity = quantity
            else:
                db.session.delete(cart_item)
                
            db.session.commit()
        else:
            cart = session.get('cart', {})
            if quantity > 0:
                cart[str(product_id)] = quantity
            else:
                cart.pop(str(product_id), None)
            session['cart'] = cart
        
        return jsonify({'message': 'Sepet güncellendi'})

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

    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        related_products = Product.query.filter_by(category=product.category).limit(4).all()
        return render_template('products/detail.html', 
                             product=product, 
                             related_products=related_products)

    @app.route('/category/<string:category_name>')
    def category_products(category_name):
        page = request.args.get('page', 1, type=int)
        sort = request.args.get('sort', 'default')
        
        if sort == 'price_asc':
            order = Product.price.asc()
        elif sort == 'price_desc':
            order = Product.price.desc()
        elif sort == 'newest':
            order = Product.created_at.desc()
        else:
            order = Product.name.asc()
        
        products = Product.query.filter_by(category=category_name)\
            .order_by(order)\
            .paginate(page=page, per_page=12)
        
        return render_template('products/category.html', 
                             products=products,
                             category=category_name,
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

    # Helper functions
    def get_cart_count():
        if current_user.is_authenticated:
            return CartItem.query.filter_by(user_id=current_user.id).count()
        else:
            return len(session.get('cart', {}))

    # Context processor
    @app.context_processor
    def utility_processor():
        return {
            'cart_count': get_cart_count()
        }

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)