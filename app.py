import os
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, Order, OrderItem

# 1. Définir les chemins absolus pour Vercel
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
css_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'css'))

# 2. Initialiser Flask en lui indiquant le dossier des templates
app = Flask(__name__, template_folder=template_dir)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialisation et données de test
with app.app_context():
    db.create_all()
    if Product.query.count() == 0:
        sample_products = [
            Product(name="Apple iPhone 15 Pro", brand="Apple", series="Apple", price_usd=1099, image_url="images/iphone15pro.jpg", specs="256Go • 8Go RAM", tag="CAMERA"),
            Product(name="Samsung Galaxy S24 Ultra", brand="Samsung", series="Samsung-S", price_usd=999, image_url="images/s24ultra.jpg", specs="512Go • 12Go RAM", tag="PERF"),
            Product(name="Samsung Galaxy A15", brand="Samsung", series="Samsung-A", price_usd=180, image_url="images/samsung_a15.jpg", specs="128Go • 6Go RAM", tag="ALL"),
            Product(name="Infinix Note 40 Pro", brand="Infinix", series="Infinix", price_usd=280, image_url="images/infinix_note40.jpg", specs="256Go • 8Go RAM", tag="BATTERY")
        ]
        db.session.bulk_save_objects(sample_products)
        db.session.commit()

# ==========================================
# 1. AUTHENTIFICATION & UTILISATEURS
# ==========================================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"message": "Cet email est déjà utilisé"}), 400

    hashed_pw = generate_password_hash(data.get('password'))
    new_user = User(
        email=data.get('email'),
        password_hash=hashed_pw,
        role=data.get('role', 'client'),
        nom=data.get('nom', ''),
        prenom=data.get('prenom', '')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Compte créé avec succès", "user": new_user.to_dict()}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()

    if user and check_password_hash(user.password_hash, data.get('password')):
        return jsonify({
            "message": "Connexion réussie", 
            "user": user.to_dict(),
            "role": user.role,  
            "user_id": user.id
        }), 200

    return jsonify({"message": "Identifiants invalides"}), 401

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'nom' in data: user.nom = data['nom']
    if 'prenom' in data: user.prenom = data['prenom']
    if 'email' in data: user.email = data['email']
    if 'role' in data: user.role = data['role']
    if 'password' in data and data['password']:
        user.password_hash = generate_password_hash(data['password'])

    db.session.commit()
    return jsonify({"message": "Utilisateur mis à jour", "user": user.to_dict()}), 200

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Utilisateur supprimé"}), 200

# ==========================================
# GESTION RÉCUPÉRATION COMPTE
# ==========================================

@app.route('/api/recover-email', methods=['POST'])
def recover_email():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    
    if user:
        return jsonify({"message": "Si cet email existe, un lien a été envoyé."}), 200
    return jsonify({"message": "Email non trouvé."}), 404

@app.route('/api/recover-phone', methods=['POST'])
def recover_phone():
    data = request.get_json()
    phone = data.get('phone')
    return jsonify({"message": f"Code OTP envoyé au {phone}"}), 200


# ==========================================
# 2. PRODUITS & CATALOGUE
# ==========================================

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all() 
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "marque_modele": p.name, 
        "brand": p.brand,
        "ecran": getattr(p, 'ecran', '6.7" AMOLED'),
        "camera": getattr(p, 'camera', '50 MP'),
        "batterie": getattr(p, 'batterie', '5000 mAh'),
        "stockage": p.specs,
        "ram": getattr(p, 'ram', '8Go'),
        "prix_approx": p.price_usd,
        "tendance": getattr(p, 'tendance', 85), 
        "photo_url": getattr(p, 'image_url', ''),
        "nom": p.name,
        "marque": p.brand,
        "prix": f"{p.price_usd} $",
        "etat": getattr(p, 'statut', 'Actif'),
        "vendeur": p.vendeur_id if p.vendeur_id else "Boutique",
        "whatsapp": "2290100000000",
        "description": p.specs
    } for p in products]), 200

@app.route('/api/vendeur/products', methods=['GET'])
def get_vendeur_products():
    vendeur_id = request.args.get('vendeur_id')
    if not vendeur_id:
        return jsonify({"message": "ID Vendeur obligatoire"}), 400
    products = Product.query.filter_by(vendeur_id=vendeur_id).all()
    return jsonify([p.to_dict() for p in products]), 200

@app.route('/api/vendeur/products', methods=['POST'])
def add_product():
    data = request.get_json()
    new_product = Product(
        name=data.get('nom'),
        brand=data.get('marque'),
        price_usd=float(data.get('prix', 0)),
        currency=data.get('devise', 'F CFA'),
        specs=data.get('description', ''),
        statut=data.get('statut', 'Actif'),
        vendeur_id=data.get('vendeur_id')
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Produit ajouté", "product": new_product.to_dict()}), 201

@app.route('/api/vendeur/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()

    if 'nom' in data: product.name = data['nom']
    if 'prix' in data: product.price_usd = float(data['prix'])
    if 'statut' in data: product.statut = data['statut']
    if 'description' in data: product.specs = data['description']

    db.session.commit()
    return jsonify({"message": "Produit mis à jour", "product": product.to_dict()}), 200

@app.route('/api/vendeur/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Produit supprimé"}), 200


# ==========================================
# 3. GESTION DES FAVORIS (CLIENT)
# ==========================================

@app.route('/api/users/<int:user_id>/favorites', methods=['GET'])
def get_favorites(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify([p.to_dict() for p in user.favorite_products]), 200

@app.route('/api/users/<int:user_id>/favorites', methods=['POST'])
def toggle_favorite(user_id):
    user = User.query.get_or_404(user_id)
    product_id = request.get_json().get('product_id')
    product = Product.query.get_or_404(product_id)

    if product in user.favorite_products:
        user.favorite_products.remove(product)
        message = "Produit retiré des favoris"
        is_favorite = False
    else:
        user.favorite_products.append(product)
        message = "Produit ajouté aux favoris"
        is_favorite = True

    db.session.commit()
    return jsonify({"message": message, "is_favorite": is_favorite}), 200


# ==========================================
# 4. GESTION DES COMMANDES
# ==========================================

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data.get('user_id')
    items_data = data.get('items', [])

    if not items_data:
        return jsonify({"message": "Le panier est vide"}), 400

    total = 0
    new_order = Order(user_id=user_id, total=0)
    db.session.add(new_order)

    for item in items_data:
        product = Product.query.get(item['product_id'])
        if product:
            item_price = product.price_usd * item['quantite']
            total += item_price
            order_item = OrderItem(
                order=new_order,
                product_id=product.id,
                quantite=item['quantite'],
                prix_unitaire=product.price_usd
            )
            db.session.add(order_item)

    new_order.total = total
    db.session.commit()

    return jsonify({"message": "Commande enregistrée avec succès", "order": new_order.to_dict()}), 201

@app.route('/api/users/<int:user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.date_creation.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    statut = request.get_json().get('statut')
    if statut:
        order.statut = statut
        db.session.commit()
        return jsonify({"message": "Statut de la commande mis à jour", "order": order.to_dict()}), 200
    return jsonify({"message": "Statut manquant"}), 400

# ==========================================
# ROUTES FRONT-END (HTML / CSS)
# ==========================================

@app.route('/')
def home():
    return render_template('Accueil-phone.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    # On utilise la variable css_dir définie en haut pour être sûr à 100% du chemin
    return send_from_directory(css_dir, filename)

# ==========================================
# ROUTE DYNAMIQUE POUR TOUTES LES PAGES HTML
# ==========================================
@app.route('/<page_name>')
def render_html_page(page_name):
    try:
        # Cela va chercher automatiquement n'importe quel fichier .html dans ton dossier templates
        return render_template(f"{page_name}.html")
    except Exception:
        # Si le fichier n'existe pas, on évite l'erreur 500 et on affiche un message propre
        return "Page introuvable (Erreur 404)", 404

# Lancement local (ignoré par Vercel)
if __name__ == '__main__':
    app.run(debug=True, port=5000)