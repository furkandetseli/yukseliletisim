# models/category.py
from extensions import db
from datetime import datetime
from slugify import slugify

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
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
    
    # Relationship with products
    products = db.relationship('Product', backref='category_ref', lazy=True)

    def __init__(self, *args, **kwargs):
        if 'slug' not in kwargs:
            kwargs['slug'] = slugify(kwargs.get('name', ''))
        super(Category, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<Category {self.name}>'

    def get_hierarchy(self):
        """Returns category hierarchy as a list"""
        hierarchy = []
        current = self
        while current is not None:
            hierarchy.append(current)
            current = current.parent
        return list(reversed(hierarchy))

    @staticmethod
    def get_tree():
        """Returns complete category tree"""
        return Category.query.filter_by(parent_id=None).all()

    def to_dict(self):
        """Convert category to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'parent_id': self.parent_id,
            'image': self.image,
            'is_active': self.is_active,
            'order': self.order,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }