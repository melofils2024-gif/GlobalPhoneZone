import os
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, Order, OrderItem

# Définir les chemins absolus pour les dossiers du projet
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(BASE_DIR, 'templates')
css_dir = os.path.join(BASE_DIR, 'css')
js_dir = os.path.join(BASE_DIR, 'js')
images_dir = os.path.join(BASE_DIR, 'images')

app = Flask(__name__, template_folder=template_dir)
CORS(app)

# Configuration DB pour Render (PostgreSQL) ou SQLite en local
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    db_path = os.path.join(BASE_DIR, 'instance', 'database.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Taux de conversion de devises de référence
RATES = {
    'USD': 1.0,
    'EUR': 0.92,
    'FCFA': 600.0,
    'XOF': 600.0
}

def to_usd(price, currency):
    """Convertit un montant d'une devise donnée vers l'USD"""
    rate = RATES.get(currency.upper(), 1.0)
    return round(float(price) / rate, 2)

def from_usd(price_usd, currency):
    """Convertit un montant USD vers la devise demandée"""
    rate = RATES.get(currency.upper(), 1.0)
    return round(float(price_usd) * rate, 2)


def seed_database():
    """Initialise et peuple la base de données si elle est vide."""
    try:
        db.create_all()

        if Product.query.count() == 0:
            # 1. Création des utilisateurs de test
            demo_seller = User.query.filter_by(email="vendeur@boutique.com").first()
            if not demo_seller:
                demo_seller = User(
                    email="vendeur@boutique.com",
                    password_hash=generate_password_hash("pass123"),
                    role="vendeur",
                    nom="Diallo",
                    prenom="Amadou",
                    phone="22997001122",
                    nom_boutique="Global Tech Express"
                )
                db.session.add(demo_seller)

            demo_client = User.query.filter_by(email="client@gmail.com").first()
            if not demo_client:
                demo_client = User(
                    email="client@gmail.com",
                    password_hash=generate_password_hash("pass123"),
                    role="client",
                    nom="Kouassi",
                    prenom="Jean",
                    phone="22995443322"
                )
                db.session.add(demo_client)
            db.session.commit()

            # 2. Catalogue des 12 meilleurs téléphones mondiaux
            best_12_phones = [
                Product(name="Apple iPhone 15 Pro Max", brand="Apple", series="Apple", price_usd=1199.0, price_original=1199.0, currency="USD", image_url="", specs="256Go • 8Go RAM • Puce A17 Pro (3nm)", tag="CAMERA", statut="Actif", condition="neuf", etat="Neuf", ecran='6.7" Super Retina XDR OLED 120Hz ProMotion', camera="48 MP Principal + 12 MP Périscope x5 + 12 MP Ultra-Wide", batterie="4422 mAh • Charge 20W + MagSafe 15W", stockage="256Go", ram="8Go", tendance=99, whatsapp="22997001122"),
                Product(name="Samsung Galaxy S24 Ultra", brand="Samsung", series="Samsung-S", price_usd=1299.0, price_original=780000.0, currency="FCFA", image_url="", specs="512Go • 12Go RAM • Snapdragon 8 Gen 3 • Stylus S-Pen", tag="PERF", statut="Actif", condition="neuf", etat="Neuf", ecran='6.8" Dynamic AMOLED 2X 120Hz QHD+ (2600 nits)', camera="200 MP Principal + 50 MP Zoom x5 + 10 MP Zoom x3 + 12 MP", batterie="5000 mAh • Charge rapide 45W", stockage="512Go", ram="12Go", tendance=98, whatsapp="22997001122"),
                Product(name="Google Pixel 8 Pro", brand="Google", series="Google", price_usd=899.0, price_original=899.0, currency="USD", image_url="", specs="256Go • 12Go RAM • Google Tensor G3 • IA Avancée", tag="CAMERA", statut="Actif", condition="neuf", etat="Neuf", ecran='6.7" Super Actua LTPO OLED 120Hz', camera="50 MP Principal + 48 MP Téléobjectif x5 + 48 MP Ultra-Wide", batterie="5050 mAh • Charge 30W", stockage="256Go", ram="12Go", tendance=95, whatsapp="22997001122"),
                Product(name="Xiaomi 14 Ultra", brand="Xiaomi", series="Xiaomi", price_usd=1099.0, price_original=1050.0, currency="EUR", image_url="", specs="512Go • 16Go RAM • Optique Leica 1 pouce", tag="CAMERA", statut="Actif", condition="neuf", etat="Neuf", ecran='6.73" AMOLED LTPO WQHD+ 120Hz', camera="50 MP Quad Leica (Capteur 1 pouce LYT-900)", batterie="5000 mAh • Charge 90W filaire / 80W sans fil", stockage="512Go", ram="16Go", tendance=94, whatsapp="22997001122"),
                Product(name="OnePlus 12", brand="OnePlus", series="OnePlus", price_usd=799.0, price_original=799.0, currency="USD", image_url="", specs="256Go • 12Go RAM • Snapdragon 8 Gen 3 • Hasselblad", tag="PERF", statut="Actif", condition="neuf", etat="Neuf", ecran='6.82" ProXDR AMOLED 120Hz 2K (4500 nits)', camera="50 MP Sony LYT-808 + 64 MP Périscope x3 + 48 MP", batterie="5400 mAh • Charge Ultra-rapide 100W", stockage="256Go", ram="12Go", tendance=93, whatsapp="22997001122"),
                Product(name="Apple iPhone 15", brand="Apple", series="Apple", price_usd=799.0, price_original=480000.0, currency="FCFA", image_url="", specs="128Go • 6Go RAM • Dynamic Island • Puce A16", tag="ALL", statut="Actif", condition="neuf", etat="Neuf", ecran='6.1" Super Retina XDR OLED', camera="48 MP Principal + 12 MP Ultra grand-angle", batterie="3349 mAh • USB-C", stockage="128Go", ram="6Go", tendance=92, whatsapp="22997001122"),
                Product(name="Samsung Galaxy A55 5G", brand="Samsung", series="Samsung-A", price_usd=380.0, price_original=230000.0, currency="FCFA", image_url="", specs="256Go • 8Go RAM • Exynos 1480 • Châssis Métal", tag="BUDGET", statut="Actif", condition="neuf", etat="Neuf", ecran='6.6" Super AMOLED 120Hz FHD+', camera="50 MP OIS + 12 MP Ultra-Wide + 5 MP Macro", batterie="5000 mAh • Charge 25W", stockage="256Go", ram="8Go", tendance=90, whatsapp="22997001122"),
                Product(name="Infinix Note 40 Pro+ 5G", brand="Infinix", series="Infinix", price_usd=290.0, price_original=175000.0, currency="FCFA", image_url="", specs="256Go • 12Go RAM • Charge 100W All-Round FastCharge", tag="BATTERY", statut="Actif", condition="neuf", etat="Neuf", ecran='6.78" AMOLED Incurvé 3D 120Hz', camera="108 MP OIS Super-Zoom + 2 MP + 2 MP", batterie="4600 mAh • Charge 100W + 20W sans fil MagCharge", stockage="256Go", ram="12Go", tendance=89, whatsapp="22997001122"),
                Product(name="Tecno Camon 30 Premier 5G", brand="Tecno", series="Tecno", price_usd=360.0, price_original=215000.0, currency="FCFA", image_url="", specs="512Go • 12Go RAM • Puce Imagerie Sony Dual", tag="CAMERA", statut="Actif", condition="neuf", etat="Neuf", ecran='6.77" LTPO AMOLED 1.5K 120Hz', camera="50 MP Sony IMX890 OIS + 50 MP Périscope + 50 MP Ultra", batterie="5000 mAh • Charge 70W", stockage="512Go", ram="12Go", tendance=88, whatsapp="22997001122"),
                Product(name="Xiaomi Redmi Note 13 Pro+ 5G", brand="Xiaomi", series="Xiaomi", price_usd=340.0, price_original=205000.0, currency="FCFA", image_url="", specs="256Go • 8Go RAM • Écran Incurvé 1.5K • IP68", tag="PERF", statut="Actif", condition="neuf", etat="Neuf", ecran='6.67" CrystalRes AMOLED 120Hz 1.5K', camera="200 MP Samsung ISOCELL HP3 OIS + 8 MP + 2 MP", batterie="5000 mAh • HyperCharge 120W", stockage="256Go", ram="8Go", tendance=88, whatsapp="22997001122"),
                Product(name="Samsung Galaxy A15", brand="Samsung", series="Samsung-A", price_usd=160.0, price_original=98000.0, currency="FCFA", image_url="", specs="128Go • 6Go RAM • Helio G99 • Super AMOLED", tag="BUDGET", statut="Actif", condition="neuf", etat="Neuf", ecran='6.5" Super AMOLED 90Hz FHD+', camera="50 MP Principal + 5 MP Ultra-Wide + 2 MP", batterie="5000 mAh • Charge 25W", stockage="128Go", ram="6Go", tendance=86, whatsapp="22997001122"),
                Product(name="Itel S24", brand="Itel", series="Itel", price_usd=110.0, price_original=68000.0, currency="FCFA", image_url="", specs="128Go • 8Go RAM (4+4) • Helio G91 Ultra", tag="BUDGET", statut="Actif", condition="neuf", etat="Neuf", ecran='6.6" Punch-hole 90Hz HD+', camera="108 MP Ultra Clear + Capteur IA", batterie="5000 mAh • Charge 18W Type-C", stockage="128Go", ram="8Go", tendance=85, whatsapp="22997001122"),
            ]
            db.session.bulk_save_objects(best_12_phones)
            db.session.commit()

            # 3. Favoris & Commande de démo pour le client de test
            p_fav = Product.query.first()
            if p_fav and demo_client:
                demo_client.favorite_products.append(p_fav)
                sample_order = Order(
                    user_id=demo_client.id,
                    total=p_fav.price_usd * 600,
                    currency="FCFA",
                    statut="En attente",
                    client_name=f"{demo_client.prenom} {demo_client.nom}",
                    client_phone=demo_client.phone
                )
                db.session.add(sample_order)
                db.session.commit()
                order_item = OrderItem(
                    order_id=sample_order.id,
                    product_id=p_fav.id,
                    quantite=1,
                    prix_unitaire=p_fav.price_usd * 600
                )
                db.session.add(order_item)
                db.session.commit()

    except Exception as e:
        print(f"[SEED] Erreur d'initialisation : {e}")
        db.session.rollback()


# Initialisation du contexte de l'application
with app.app_context():
    seed_database()


# ==========================================
# 1. AUTHENTIFICATION & UTILISATEURS
# ==========================================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    
    if not email or not data.get('password'):
        return jsonify({"message": "Email et mot de passe requis"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Cet email est déjà utilisé"}), 400

    hashed_pw = generate_password_hash(data.get('password'))
    new_user = User(
        email=email,
        password_hash=hashed_pw,
        role=data.get('role', 'client'),
        nom=data.get('nom', '').strip(),
        prenom=data.get('prenom', '').strip(),
        phone=data.get('phone', '').strip(),
        nom_boutique=data.get('nom_boutique', data.get('nom', '')).strip()
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        "message": "Compte créé avec succès",
        "user": new_user.to_dict(),
        "user_id": new_user.id,
        "role": new_user.role,
        "nom": new_user.nom,
        "prenom": new_user.prenom
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        return jsonify({
            "message": "Connexion réussie",
            "user": user.to_dict(),
            "role": user.role,
            "user_id": user.id,
            "id": user.id,
            "nom": user.nom,
            "prenom": user.prenom,
            "nom_boutique": user.nom_boutique,
            "phone": user.phone
        }), 200

    return jsonify({"message": "Identifiants invalides"}), 401

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}

    if 'nom' in data: user.nom = data['nom']
    if 'prenom' in data: user.prenom = data['prenom']
    if 'email' in data: user.email = data['email']
    if 'phone' in data: user.phone = data['phone']
    if 'nom_boutique' in data: user.nom_boutique = data['nom_boutique']
    if 'password' in data and data['password']:
        user.password_hash = generate_password_hash(data['password'])

    db.session.commit()
    return jsonify({"message": "Profil mis à jour", "user": user.to_dict()}), 200


# ==========================================
# 2. PRODUITS & CATALOGUE MULTI-DEVISES
# ==========================================

@app.route('/api/products', methods=['GET'])
def get_products():
    currency = request.args.get('currency', 'USD').upper()
    brand = request.args.get('brand')
    tag = request.args.get('tag')
    vendeur_only = request.args.get('vendeur_only')
    
    query = Product.query
    
    if brand and brand != 'ALL':
        if brand == 'Samsung-S':
            query = query.filter(Product.series == 'Samsung-S')
        elif brand == 'Samsung-A':
            query = query.filter(Product.series == 'Samsung-A')
        else:
            query = query.filter(Product.brand.ilike(f"%{brand}%"))
            
    if tag and tag != 'ALL':
        query = query.filter(Product.tag == tag)
        
    if vendeur_only == 'true':
        query = query.filter(Product.vendeur_id.isnot(None))

    products = query.order_by(Product.tendance.desc()).all()
    
    results = []
    for p in products:
        item = p.to_dict()
        item['price_converted'] = from_usd(p.price_usd, currency)
        item['active_currency'] = currency
        results.append(item)

    return jsonify(results), 200

@app.route('/api/ranking', methods=['GET'])
def get_ranking():
    return get_products()

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict()), 200

@app.route('/api/products/seller/<int:vendeur_id>', methods=['GET'])
def get_seller_products(vendeur_id):
    products = Product.query.filter_by(vendeur_id=vendeur_id).order_by(Product.id.desc()).all()
    return jsonify([p.to_dict() for p in products]), 200

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.get_json() or {}
    
    name = data.get('name') or data.get('nom')
    brand = data.get('brand') or data.get('marque')
    price_input = float(data.get('price') or data.get('prix') or 0)
    currency_input = (data.get('currency') or data.get('devise') or 'FCFA').upper()
    
    if not name or not brand:
        return jsonify({"message": "Nom et marque obligatoires"}), 400

    price_usd_calc = to_usd(price_input, currency_input)

    new_product = Product(
        name=name,
        brand=brand,
        series=data.get('series', brand),
        price_usd=price_usd_calc,
        price_original=price_input,
        currency=currency_input,
        image_url=data.get('image_url', ''),
        specs=data.get('desc', data.get('description', data.get('specs', ''))),
        tag=data.get('tag', 'ALL'),
        statut=data.get('statut', 'Actif'),
        condition=data.get('condition', 'neuf'),
        etat=data.get('etat', 'Neuf' if data.get('condition', 'neuf') == 'neuf' else "D'occasion"),
        ecran=data.get('ecran', '6.7" AMOLED'),
        camera=data.get('camera', '50 MP'),
        batterie=data.get('batterie', '5000 mAh'),
        stockage=data.get('stockage', '128Go'),
        ram=data.get('ram', '8Go'),
        tendance=int(data.get('tendance', 85)),
        whatsapp=data.get('whatsapp', '2290100000000'),
        vendeur_id=data.get('seller_id', data.get('vendeur_id'))
    )
    
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Produit publié avec succès", "product": new_product.to_dict()}), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}

    if 'name' in data or 'nom' in data: product.name = data.get('name', data.get('nom'))
    if 'brand' in data or 'marque' in data: product.brand = data.get('brand', data.get('marque'))
    
    if 'price' in data or 'prix' in data:
        p_val = float(data.get('price', data.get('prix')))
        curr = data.get('currency', product.currency or 'FCFA').upper()
        product.price_original = p_val
        product.currency = curr
        product.price_usd = to_usd(p_val, curr)

    if 'statut' in data: product.statut = data['statut']
    if 'condition' in data: product.condition = data['condition']
    if 'etat' in data: product.etat = data['etat']
    if 'desc' in data or 'specs' in data: product.specs = data.get('desc', data.get('specs'))
    if 'ecran' in data: product.ecran = data['ecran']
    if 'camera' in data: product.camera = data['camera']
    if 'batterie' in data: product.batterie = data['batterie']
    if 'stockage' in data: product.stockage = data['stockage']
    if 'ram' in data: product.ram = data['ram']

    db.session.commit()
    return jsonify({"message": "Produit mis à jour", "product": product.to_dict()}), 200

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Produit supprimé avec succès"}), 200


# ==========================================
# 3. GESTION DES FAVORIS (CLIENT)
# ==========================================

@app.route('/api/users/<int:user_id>/favorites', methods=['GET'])
@app.route('/api/favorites/<int:user_id>', methods=['GET'])
def get_favorites(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify([p.to_dict() for p in user.favorite_products]), 200

@app.route('/api/users/<int:user_id>/favorites', methods=['POST'])
@app.route('/api/favorites', methods=['POST'])
def add_favorite(user_id=None):
    data = request.get_json() or {}
    uid = user_id or data.get('user_id')
    user = User.query.get_or_404(uid)
    
    product_id = data.get('product_id')
    product = None
    
    if product_id:
        product = Product.query.get(product_id)
    elif data.get('name'):
        product = Product.query.filter_by(name=data.get('name')).first()

    if not product:
        return jsonify({"message": "Produit introuvable"}), 404

    if product not in user.favorite_products:
        user.favorite_products.append(product)
        db.session.commit()
        return jsonify({"message": "Ajouté aux favoris avec succès ❤️", "is_favorite": True, "product": product.to_dict()}), 200
    
    return jsonify({"message": "Ce téléphone est déjà dans vos favoris", "is_favorite": True}), 200

@app.route('/api/users/<int:user_id>/favorites/<int:product_id>', methods=['DELETE'])
@app.route('/api/favorites/<int:user_id>/<int:product_id>', methods=['DELETE'])
def remove_favorite(user_id, product_id):
    user = User.query.get_or_404(user_id)
    product = Product.query.get_or_404(product_id)

    if product in user.favorite_products:
        user.favorite_products.remove(product)
        db.session.commit()
        return jsonify({"message": "Retiré des favoris"}), 200

    return jsonify({"message": "Non présent dans les favoris"}), 404

@app.route('/api/users/<int:user_id>/favorites', methods=['DELETE'])
@app.route('/api/favorites/<int:user_id>', methods=['DELETE'])
def clear_all_favorites(user_id):
    user = User.query.get_or_404(user_id)
    user.favorite_products.clear()
    db.session.commit()
    return jsonify({"message": "Tous les favoris ont été supprimés"}), 200


# ==========================================
# 4. GESTION DES COMMANDES
# ==========================================

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    items_data = data.get('items', [])
    product_id = data.get('product_id')
    currency = data.get('currency', 'FCFA')

    user = User.query.get(user_id) if user_id else None
    client_name = data.get('client_name') or (f"{user.prenom} {user.nom}".strip() if user else "Client Anonyme")
    client_phone = data.get('client_phone') or (user.phone if user else "22900000000")

    if product_id and not items_data:
        items_data = [{'product_id': product_id, 'quantite': data.get('quantite', 1)}]

    if not items_data:
        return jsonify({"message": "Aucun article sélectionné"}), 400

    total = 0.0
    new_order = Order(
        user_id=user_id if user_id else (user.id if user else 2),
        total=0,
        currency=currency,
        client_name=client_name,
        client_phone=client_phone,
        statut="En attente"
    )
    db.session.add(new_order)

    for item in items_data:
        product = Product.query.get(item['product_id'])
        if product:
            converted_unit = from_usd(product.price_usd, currency)
            item_total = converted_unit * item.get('quantite', 1)
            total += item_total
            order_item = OrderItem(
                order=new_order,
                product_id=product.id,
                quantite=item.get('quantite', 1),
                prix_unitaire=converted_unit
            )
            db.session.add(order_item)

    new_order.total = round(total, 2)
    db.session.commit()

    return jsonify({"message": "Commande enregistrée avec succès", "order": new_order.to_dict()}), 201

@app.route('/api/users/<int:user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.date_creation.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200

@app.route('/api/orders/seller/<int:vendeur_id>', methods=['GET'])
def get_seller_orders(vendeur_id):
    orders = (
        Order.query.join(Order.items)
        .join(OrderItem.product)
        .filter(Product.vendeur_id == vendeur_id)
        .distinct()
        .order_by(Order.date_creation.desc())
        .all()
    )
    return jsonify([o.to_dict() for o in orders]), 200

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    statut = request.get_json().get('statut')
    if statut:
        order.statut = statut
        db.session.commit()
        return jsonify({"message": "Statut mis à jour", "order": order.to_dict()}), 200
    return jsonify({"message": "Statut manquant"}), 400


# ==========================================
# 5. ASSISTANT INTELLIGENT DE RECOMMANDATION
# ==========================================

@app.route('/api/assistant/recommend', methods=['POST'])
def recommend_phone():
    data = request.get_json() or {}
    
    budget_raw = data.get('budget')
    currency = data.get('currency', 'FCFA').upper()
    priority = data.get('priority', 'ALL').upper()
    brand = data.get('brand', 'ALL')
    
    max_budget_usd = None
    if budget_raw and float(budget_raw) > 0:
        max_budget_usd = to_usd(float(budget_raw), currency)

    query = Product.query
    
    if brand and brand != 'ALL':
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
        
    products = query.all()
    
    scored_products = []
    for p in products:
        score = p.tendance or 80
        
        if max_budget_usd:
            if p.price_usd <= max_budget_usd:
                ratio = p.price_usd / max_budget_usd
                score += int((1 - abs(1 - ratio)) * 20)
            else:
                score -= int((p.price_usd - max_budget_usd) / 10)

        if priority == 'CAMERA':
            if p.tag == 'CAMERA' or '200 MP' in (p.camera or '') or 'Leica' in (p.specs or '') or 'Pro' in p.name:
                score += 30
        elif priority == 'BATTERY':
            if p.tag == 'BATTERY' or '5000' in (p.batterie or '') or '5400' in (p.batterie or ''):
                score += 30
        elif priority == 'PERF':
            if p.tag == 'PERF' or '12Go' in (p.ram or '') or '16Go' in (p.ram or '') or 'Ultra' in p.name:
                score += 30
        elif priority == 'BUDGET':
            if p.price_usd <= 400:
                score += 25

        reason = "Excellent rapport performance / prix mondial."
        if priority == 'CAMERA':
            reason = f"Recommandé pour sa caméra exceptionnelle : {p.camera}."
        elif priority == 'BATTERY':
            reason = f"Idéal pour son autonomie record avec {p.batterie}."
        elif priority == 'PERF':
            reason = f"Parfait pour le gaming et la puissance brute avec {p.ram} de RAM."
        elif max_budget_usd and p.price_usd <= max_budget_usd:
            reason = f"S'intègre parfaitement dans votre budget de {budget_raw} {currency}."

        item = p.to_dict()
        item['match_score'] = min(max(score, 50), 99)
        item['recommendation_reason'] = reason
        item['price_converted'] = from_usd(p.price_usd, currency)
        item['active_currency'] = currency
        
        scored_products.append(item)

    scored_products.sort(key=lambda x: x['match_score'], reverse=True)
    top_recommendations = scored_products[:3]

    return jsonify({
        "status": "success",
        "recommendations": top_recommendations,
        "count": len(top_recommendations)
    }), 200


# ==========================================
# 6. RÉCUPÉRATION COMPTE
# ==========================================

@app.route('/api/recover-email', methods=['POST'])
def recover_email():
    data = request.get_json() or {}
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"message": "Si cet email existe, un lien a été envoyé."}), 200
    return jsonify({"message": "Email non trouvé."}), 404

@app.route('/api/recover-phone', methods=['POST'])
def recover_phone():
    data = request.get_json() or {}
    phone = data.get('phone')
    return jsonify({"message": f"Code OTP envoyé au {phone}"}), 200


# ==========================================
# 7. ROUTES FRONT-END (HTML, CSS, JS, IMAGES)
# ==========================================

@app.route('/')
def home():
    return render_template('Accueil-phone.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(css_dir, filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(js_dir, filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory(images_dir, filename)

@app.route('/<page_name>')
def render_html_page(page_name):
    if page_name.startswith('api'):
        return jsonify({"error": "API route not found"}), 404
        
    try:
        if page_name.endswith('.html'):
            page_name = page_name[:-5]
        return render_template(f"{page_name}.html")
    except Exception:
        return "Page introuvable (Erreur 404)", 404
    
@app.route('/reset-database-urgente')
def reset_database_urgente():
    try:
        # Supprime toutes les anciennes tables obsolètes
        db.drop_all()
        # Recrée toutes les tables avec la structure à jour
        db.create_all()
        # Ré-injecte les données de base (les 12 téléphones par défaut)
        if 'seed_database' in globals():
            seed_database()
        return "Succès : La base de données PostgreSQL a été entièrement réinitialisée et mise à jour !"
    except Exception as e:
        return f"Erreur lors de la réinitialisation : {str(e)}", 500
    
with app.app_context():
    db.drop_all()
    db.create_all()
    if 'seed_database' in globals():
        seed_database()


if __name__ == '__main__':
    app.run(debug=True, port=5000)