# backend/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from app import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email adresi zaten kayıtlı'}), 400
    
    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data.get('phone', '')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'Kayıt başarılı'}), 201

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(user)
        return jsonify({'message': 'Giriş başarılı'})
    
    return jsonify({'error': 'Geçersiz email veya şifre'}), 401

@auth_bp.route('/api/auth/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Çıkış yapıldı'})

@auth_bp.route('/api/auth/reset-password-request', methods=['POST'])
def reset_password_request():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    
    if user:
        token = user.get_reset_password_token()
        # Burada email gönderme işlemi yapılacak
        return jsonify({'message': 'Şifre sıfırlama talimatları email adresinize gönderildi'})
    
    return jsonify({'error': 'Email adresi bulunamadı'}), 404

@auth_bp.route('/api/auth/reset-password/<token>', methods=['POST'])
def reset_password(token):
    user = User.verify_reset_password_token(token)
    if not user:
        return jsonify({'error': 'Geçersiz token'}), 400
    
    data = request.json
    user.set_password(data['password'])
    db.session.commit()
    
    return jsonify({'message': 'Şifre başarıyla değiştirildi'})