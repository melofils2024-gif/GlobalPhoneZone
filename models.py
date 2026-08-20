from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Table d'association pour les favoris (Many-to-Many entre User et Product)
favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='client') # 'client', 'vendeur', 'admin'
    nom = db.Column(db.String(80))
    prenom = db.Column(db.String(80))
    phone = db.Column(db.String(20), nullable=True) # À ajouter sous prenom
    
    # Relations
    products = db.relationship('Product', backref='vendeur', lazy=True)
    orders = db.relationship('Order', backref='client', lazy=True)
    favorite_products = db.relationship('Product', secondary=favorites, lazy='subquery',
                                        backref=db.backref('favorited_by', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "nom": self.nom,
            "prenom": self.prenom,
        }

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(80))
    series = db.Column(db.String(80))
    price_usd = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(20), default='F CFA')
    image_url = db.Column(db.String(255))
    specs = db.Column(db.String(255))
    tag = db.Column(db.String(50))
    statut = db.Column(db.String(50), default='Actif')
    vendeur_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.name,
            "marque": self.brand,
            "series": self.series,
            "prix": self.price_usd,
            "devise": self.currency,
            "image_url": self.image_url,
            "description": self.specs,
            "tag": self.tag,
            "statut": self.statut,
            "vendeur_id": self.vendeur_id,
            "ecran": "AMOLED",
            "camera": "50 MP",
            "batterie": "5000 mAh",
            "stockage": "128Go",
            "ram": "8Go",
            "tendance": 85
        }

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    statut = db.Column(db.String(50), default='En attente')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        # Récupérer le nom du premier produit de la commande (pour l'affichage simple côté vendeur)
        first_product_name = self.items[0].product.name if self.items and self.items[0].product else "Articles multiples"

        return {
            "id": self.id,
            "user_id": self.user_id,
            # On récupère le nom du client grâce à la relation backref='client'
            "client_name": f"{self.client.prenom or ''} {self.client.nom or ''}".strip() if self.client else "Client Anonyme",
            # On met un faux numéro en attendant d'avoir une vraie colonne 'phone' dans la table User
            "client_phone": "22900000000", 
            "product_name": first_product_name,
            "total": self.total,
            "statut": self.statut,
            "date_creation": self.date_creation.strftime('%Y-%m-%d %H:%M:%S'),
            "items": [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else "Produit supprimé",
            "quantite": self.quantite,
            "prix_unitaire": self.prix_unitaire
        }