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
    nom = db.Column(db.String(80), default='')
    prenom = db.Column(db.String(80), default='')
    phone = db.Column(db.String(30), default='')
    nom_boutique = db.Column(db.String(120), default='')
    
    # Relations
    products = db.relationship('Product', backref='vendeur', lazy=True, cascade="all, delete-orphan")
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
            "phone": self.phone or '',
            "nom_boutique": self.nom_boutique or ''
        }

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(80), nullable=False)
    series = db.Column(db.String(80), default='')
    price_usd = db.Column(db.Float, nullable=False)
    price_original = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(20), default='USD') # 'USD', 'EUR', 'FCFA'
    image_url = db.Column(db.String(255), default='')
    specs = db.Column(db.String(255), default='')
    tag = db.Column(db.String(50), default='ALL') # 'PERF', 'CAMERA', 'BATTERY', 'BUDGET', 'ALL'
    statut = db.Column(db.String(50), default='Actif')
    
    # Prise en charge Neuf / Occasion
    condition = db.Column(db.String(30), default='neuf') # 'neuf' ou 'occasion'
    etat = db.Column(db.String(80), default='Neuf')        # 'Comme neuf (Bat. 90%)', 'Très bon état', etc.
    
    # Caractéristiques détaillées
    ecran = db.Column(db.String(120), default='6.7" AMOLED 120Hz')
    camera = db.Column(db.String(120), default='50 MP + 12 MP')
    batterie = db.Column(db.String(120), default='5000 mAh')
    stockage = db.Column(db.String(80), default='256Go')
    ram = db.Column(db.String(80), default='8Go')
    tendance = db.Column(db.Integer, default=85) # 0 à 100
    whatsapp = db.Column(db.String(30), default='2290100000000')
    
    vendeur_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        vendeur_name = "Boutique Officielle"
        if self.vendeur:
            vendeur_name = self.vendeur.nom_boutique or f"{self.vendeur.prenom} {self.vendeur.nom}".strip() or f"Vendeur #{self.vendeur_id}"
            
        return {
            "id": self.id,
            "name": self.name,
            "nom": self.name,
            "brand": self.brand,
            "marque": self.brand,
            "series": self.series,
            "price_usd": self.price_usd,
            "prix": self.price_original if self.price_original else self.price_usd,
            "price_original": self.price_original or self.price_usd,
            "currency": self.currency or 'USD',
            "devise": self.currency or 'USD',
            "condition": self.condition or 'neuf',
            "etat": self.etat or ('Neuf' if self.condition == 'neuf' else 'D\'occasion'),
            "image_url": self.image_url,
            "specs": self.specs,
            "description": self.specs,
            "tag": self.tag,
            "statut": self.statut,
            "vendeur_id": self.vendeur_id,
            "vendeur": vendeur_name,
            "ecran": self.ecran or '6.7" AMOLED',
            "camera": self.camera or '50 MP',
            "batterie": self.batterie or '5000 mAh',
            "stockage": self.stockage or '256Go',
            "ram": self.ram or '8Go',
            "tendance": self.tendance or 85,
            "whatsapp": self.whatsapp or (self.vendeur.phone if self.vendeur and self.vendeur.phone else '2290100000000')
        }

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(20), default='FCFA')
    statut = db.Column(db.String(50), default='En attente') # 'En attente', 'Confirmé', 'Livré', 'Annulé'
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    client_phone = db.Column(db.String(30), default='')
    client_name = db.Column(db.String(120), default='')
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        first_product_name = self.items[0].product.name if self.items and self.items[0].product else "Articles"
        client_display = self.client_name or (f"{self.client.prenom or ''} {self.client.nom or ''}".strip() if self.client else "Client Anonyme")
        phone_display = self.client_phone or (self.client.phone if self.client else "22900000000")

        return {
            "id": self.id,
            "user_id": self.user_id,
            "client_name": client_display,
            "client_phone": phone_display,
            "product_name": first_product_name,
            "total": self.total,
            "currency": self.currency,
            "statut": self.statut,
            "date_creation": self.date_creation.strftime('%Y-%m-%d %H:%M'),
            "items": [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantite = db.Column(db.Integer, default=1)
    prix_unitaire = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else "Produit retiré",
            "quantite": self.quantite,
            "prix_unitaire": self.prix_unitaire
        }