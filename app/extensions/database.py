from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime

db = SQLAlchemy()

# Tabella di associazione per la relazione molti-a-molti tra utenti e ruoli
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

# Tabella di associazione per la relazione molti-a-molti tra Product e Category
product_categories = db.Table('product_categories',
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)
    
# Definizione della classe User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique = True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    roles = db.relationship('Role', secondary=user_roles, backref='users', lazy = True)
    profiles = db.relationship('Profile', backref='user', lazy=True)
    products = db.relationship('Product', backref='user', lazy = True)
    addresses = db.relationship('Address', backref='users', lazy=True)
    cart_items = db.relationship('Cart', backref='user', lazy=True)
    orders = db.relationship('Order', lazy = True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

        # Aggiunge il ruolo 'buyer' di default
        buyer_role = Role.query.filter_by(name='buyer').first()
        if not buyer_role:
            buyer_role = Role(name='buyer')
            db.session.add(buyer_role)
            db.session.commit()
        self.roles.append(buyer_role)


    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique = True, nullable=False)
    surname = db.Column(db.String(20), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    #products = db.relationship('Product', backref='profile')

    def __init__(self, name, surname, birth_date, user_id, image_url='https://static.vecteezy.com/ti/vettori-gratis/p1/2318271-icona-profilo-utente-vettoriale.jpg'):
        self.name = name
        self.surname = surname
        self.birth_date = birth_date
        self.image_url = image_url
        self.user_id = user_id

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    street = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    province = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False)

    # Chiave esterna per collegare l'indirizzo all'utente
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, street, city, postal_code, province, country, user_id):
        self.street = street
        self.city = city
        self.postal_code = postal_code
        self.country = country
        self.user_id = user_id
        self.province = province

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    availability = db.Column(db.Integer, nullable = False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 

    categories = db.relationship('Category', secondary=product_categories, backref='products')
    in_carts = db.relationship('Cart', backref='product', lazy = True)


    def __init__(self, name, price, user_id, description, categories, availability = 1, image_url = 'https://img.freepik.com/vettori-premium/un-disegno-di-una-scarpa-con-sopra-la-parola-scarpa_410516-82664.jpg'):
        user = db.session.get(User, int(user_id))
        if not user or not user.has_role('seller'):
            raise ValueError("Il profilo non appartiene a un utente con il ruolo di seller.")
        self.name = name
        self.price = price
        self.image_url = image_url
        self.description = description
        self.availability = availability
        self.user_id = user_id
        for c in categories:
            self.categories.append(c)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable = False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable = False)

    def __init__(self, quantity, user_id, product_id):
        self.quantity = quantity
        self.user_id = user_id
        self.product_id = product_id

#class OrderProduct(db.Model):
#    __tablename__ = 'order_products'
#    
#    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
#    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
#    
#    # Quantità di prodotto acquistato
#    quantity = db.Column(db.Integer, nullable=False)
#    
#    # Relazioni
#    order = db.relationship('Order', backref='order_products')
#    product = db.relationship('Product', backref='order_products')
#
#    def __init__(self, order_id, product_id, quantity):
#        self.order_id = order_id
#        self.product_id = product_id
#        self.quantity = quantity
#
#class Order(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    order_date = db.Column(db.Date, nullable=False)
#    total_price = db.Column(db.Float, nullable=False)
#
#    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
#    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=True)
#
#    # Relazione con la tabella intermedia 'OrderProduct'
#    products = db.relationship('OrderProduct', backref='order')
#
#    def __init__(self, user_id, address_id):
#        self.user_id = user_id
#        self.address_id = address_id
#
#
#
#
#
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)
    
    
    # Relazione con l'indirizzo (dove spedire l'ordine)
    address = db.relationship('Address', backref='order', lazy = True)

    # Relazione con i prodotti attraverso tabella intermedia OrderProduct
    products = db.relationship('OrderProduct', backref='order', lazy = True)

    def __init__(self, user_id, address_id, total_price):
        self.user_id = user_id
        self.address_id = address_id
        self.total_price = total_price
        
class OrderProduct(db.Model):
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    
    # Quantità di prodotto acquistato
    quantity = db.Column(db.Integer, nullable=False)
    
    # Relazioni
    product = db.relationship('Product', lazy = True)

    def __init__(self, order_id, product_id, quantity):
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  

    def __init__(self, name):
        self.name = name

def add_user(name, surname, birth_date, username, password):
    # Crea l'utente
        user = User(
            name=name,
            surname=surname,
            birth_date=datetime.strptime(birth_date, '%Y-%m-%d').date(),
            username=username,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        
        # Aggiungi l'utente alla sessione
        db.session.add(user)
        db.session.commit()

        # Crea un profilo di default per l'utente appena creato
        profile = Profile(
            name=user.name,
            surname=user.surname,
            user_id=user.id
        )
        
        # Aggiungi il profilo alla sessione
        db.session.add(profile)
        db.session.commit()
        
# Da chiamare solo quando serve popolare la tabella Role
def add_roles():
    roles = ['admin', 'seller', 'buyer']
    for role_name in roles:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            new_role = Role(name=role_name)
            db.session.add(new_role)
            db.session.commit()

# Funzione per popolare la tabella Category
def add_categories():
    categories_list = ['Elettronica','Abbigliamento','Casa e Giardino','Sport e Tempo Libero','Giochi e Giocattoli','Alimentari','Libri e Riviste','Salute e Bellezza','Arredamento','Auto e Moto','Fai da te','Musica','Film e TV','Animali domestici','Strumenti Musicali','Telefonia','Arte e Collezionismo','Viaggi','Tecnologia','Orologi e Gioielli','Altro']
    for nome_categoria in categories_list:
        categoria = Category(name=nome_categoria)
        db.session.add(categoria)
    db.session.commit()

################Tutte le altre funzioni non sono necessarie###############
# Dato un utente preesistente, aggiunge il ruolo passato come parametro(nel caso non sia presente in user.roles)
def set_user_with_role(user, role_name):
    role = Role.query.filter_by(name=role_name).first()
    if user and role and (role not in user.roles):
        user.roles.append(role)
        db.session.commit()

# Data una lista di utenti, popola la tabella User e inizializza il profilo di default
def add_users(user_list):
    for user_data in user_list:
        # Crea l'utente
        user = User(
            name=user_data['name'],
            surname=user_data['surname'],
            birth_date=datetime.strptime(user_data['birth_date'], '%Y-%m-%d').date(),
            username=user_data['username'],
            password=generate_password_hash(user_data['password'], method='pbkdf2:sha256')
        )
        
        # Aggiungi l'utente alla sessione
        db.session.add(user)
        db.session.commit()

        # Crea un profilo di default per l'utente appena creato
        profile = Profile(
            name=user.name,
            surname=user.surname,
            user_id=user.id
        )
        
        # Aggiungi il profilo alla sessione
        db.session.add(profile)
        db.session.commit()

# Data una lista di prodotti, popola la tabella Products e collega i prodotti all'unico profilo collegato allo user che ha ruolo admin
def add_products(products_list):
    first_seller = User.query.filter(User.roles.any(Role.name == 'seller')).first()
    if first_seller:
        for elem in products_list:
            existing_product = Product.query.filter_by(name=elem['name']).first()
            # Controlla se il prodotto esiste già
            if not existing_product:
                # Recupera o crea le categorie per il prodotto corrente
                categories = elem.get('categories', [])  # Ottiene la lista delle categorie dal dizionario prodotto
                category_objects = []

                # Itera sulle categorie per trovare o creare gli oggetti Category corrispondenti
                for category_name in categories:
                    category = Category.query.filter_by(name=category_name).first()
                    if not category:
                        category = Category.query.filter_by(name='Altro').first()
                    category_objects.append(category)

                # Crea e aggiungi il prodotto al database
                prod = Product(
                    name=elem['name'],
                    price=elem['price'],
                    user_id=first_seller.id,
                    description=elem['description'],
                    availability=elem['availability'],
                    categories=category_objects  # Aggiunge le categorie al prodotto
                )
                
                db.session.add(prod)
                db.session.commit()

# Funzione per popolare la tabella Category
def add_categories(categories_list):
    for nome_categoria in categories_list:
        categoria = Category.query.filter_by(name=nome_categoria).first()
        # Controlla se la categoria esiste già nel database
        if not categoria:
            # Se la categoria non esiste, aggiungila
            nuova_categoria = Category(name=nome_categoria)
            db.session.add(nuova_categoria)
            db.session.commit()

# Data una lista di interi, elimina i prodotti che hanno quegli id
def delete_products_by_ids(ids):
    # Recupera i prodotti con gli ID specificati
    products_to_delete = Product.query.filter(Product.id.in_(ids)).all()
    
    # Elimina i prodotti dalla sessione
    for product in products_to_delete:
        db.session.delete(product)
    
    # Commit delle modifiche
    db.session.commit()
    
def create_order(user_id, address_id, cart_items):
    order = Order(user_id=user_id, address_id=address_id)
    db.session.add(order)
    db.session.commit()
    
    for product_id, quantity in cart_items:
        print(f'product_id:{product_id}')
        print(f'quantity:{quantity}')
        product = Product.query.get(product_id)
        if product:
            order_product = OrderProduct(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(order_product)
            db.session.commit()
        
    return order

def get_user_orders(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    result = []
    
    for order in orders:
        products = []
        
        for order_product in order.products:
            product = Product.query.get(order_product.product_id)
            products.append({
                'name': product.name,
                'price': product.price,
                'quantity': order_product.quantity
            })
            
        result.append({
            'id': order.id,
            'date': order.order_date,
            'products': products
        })
    
    return result