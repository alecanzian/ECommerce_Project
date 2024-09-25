import time
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, false
from werkzeug.security import generate_password_hash
from datetime import datetime


db = SQLAlchemy()

# Tabella di associazione per la relazione molti-a-molti tra utenti e ruoli
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

# Tabella di associazione per la relazione molti-a-molti tra Product e Category
#product_categories = db.Table('product_categories',
#    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
#    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
#)
    
# Definizione della classe User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique = True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

    roles = db.relationship('Role', secondary=user_roles, backref='users', lazy = True)
    profiles = db.relationship('Profile', backref='user', lazy=True)
    products = db.relationship('Product', backref='user', lazy = True)
    addresses = db.relationship('Address', backref='users', lazy=True)
    orders = db.relationship('Order', backref = 'user', lazy = True)
    #cart_items = db.relationship('Cart', backref='user', lazy=True)
    cards = db.relationship('Card', backref = 'user', lazy = True)
    seller_information = db.relationship('SellerInformation', backref='user', uselist=False, lazy=True)
    #seller_information = db.relationship('SellerInformation', backref=db.backref('user', uselist=False), lazy = True)


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
    @property
    def is_valid(self):
        if not self.username or not self.password:
            return False
        return True

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique = True, nullable=False)
    surname = db.Column(db.String(20), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    cart_items = db.relationship('Cart', backref='profile', lazy=True)

    def __init__(self, name, surname, birth_date, user_id, image_url='https://static.vecteezy.com/ti/vettori-gratis/p1/2318271-icona-profilo-utente-vettoriale.jpg'):
        self.name = name
        self.surname = surname
        self.birth_date = birth_date
        self.image_url = image_url
        self.user_id = user_id
    @property
    def is_valid(self):
        if not self.name or not self.surname or not self.birth_date or not self.image_url or not self.user_id:
            return False
        return True

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    street = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    province = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False)

    # Chiave esterna per collegare l'indirizzo all'utente
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('street', 'city', 'postal_code', 'province', 'country', 'user_id', name='unique_address'),
    )

    def __init__(self, street, city, postal_code, province, country, user_id):
        self.street = street
        self.city = city
        self.postal_code = postal_code
        self.country = country
        self.user_id = user_id
        self.province = province
    @property
    def is_valid(self):
        if not self.street or not self.city or not self.postal_code or not self.province or not self.country or not self.user_id:
            return False
        return True

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique = True,nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    availability = db.Column(db.Integer, nullable = False)

    #profile_id = db.Column(db.Integer, db.ForeignKey('profile.id', ondelete = 'SET NULL'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False) 

    #categories = db.relationship('Category', secondary=product_categories, backref='products')
    category = db.relationship('Category', backref='products')
    in_carts = db.relationship('Cart', backref='product', lazy = True)


    def __init__(self, name, price, user_id, description, category_id, availability = 1, image_url = 'https://img.freepik.com/vettori-premium/un-disegno-di-una-scarpa-con-sopra-la-parola-scarpa_410516-82664.jpg'):
        self.name = name
        self.price = price
        self.image_url = image_url
        self.description = description
        self.availability = availability
        self.user_id = user_id
        self.category_id = category_id
    @property
    def is_valid(self):
        if not self.name or not self.price or not self.image_url or not self.description or not self.user_id or not self.category_id:
            return False
        return True

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable = False)

    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable = False)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable = False)

    __table_args__ = (db.UniqueConstraint('product_id', 'profile_id', name='unique_product_profile'),)

    def __init__(self, quantity, product_id, profile_id):
        self.quantity = quantity
        #self.user_id = user_id
        self.product_id = product_id
        self.profile_id = profile_id
    @property
    def is_valid(self):
        if not self.quantity or not self.product_id or not self.profile_id:
            return False
        return True

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255),nullable = False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Relazione con i prodotti attraverso tabella intermedia OrderProduct
    products = db.relationship('OrderProduct', backref='order', lazy = True)

    def __init__(self, user_id, address, total_price):
        self.user_id = user_id
        self.total_price = total_price
        self.address = address
    @property
    def is_valid(self):
        if not self.order_date or not self.address or not self.user_id:
            return False
        return True

class OrderProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(50),nullable = False)
    seller_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable = False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete = 'SET NULL'))
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'),nullable = False)

    product = db.relationship('Product', backref = 'in_order', lazy = True)
    state = db.relationship('State', backref = 'order_product', lazy = True)

    def __init__(self, order_id, product_id, product_name, quantity, seller_id):
        self.order_id = order_id
        self.product_id = product_id
        self.product_name = product_name
        self.quantity = quantity
        self.seller_id = seller_id
        self.state = State.query.filter_by(name = 'Ordinato').first()
    @property
    def is_valid(self):
        if not self.quantity or not self.timestamp or not self.product_name or not self.seller_id or not self.order_id or not self.state_id:
            return False
        return True

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name
    @property
    def is_valid(self):
        if not self.name:
            return False
        return True

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  

    def __init__(self, name):
        self.name = name
    @property
    def is_valid(self):
        if not self.name:
            return False
        return True

class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True,nullable = False)

    def __init__(self, name):
        self.name = name
    @property
    def is_valid(self):
        if not self.name:
            return False
        return True
        
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    product_name = db.Column(db.String(50),nullable = False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

    def __init__(self,sender_id, receiver_id,type,product_name, order_id):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.type = type
        self.product_name = product_name
        self.order_id = order_id
    @property
    def is_valid(self):
        if not self.type or not self.timestamp or not self.product_name or not self.sender_id or not self.receiver_id or not self.order_id:
            return False
        return True

class Card(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    pan = db.Column(db.String(256), nullable = False)
    last_digits = db.Column(db.String(4), nullable = False)
    expiration_month = db.Column(db.String(256), nullable = False)
    expiration_year = db.Column(db.String(256), nullable = False)
    card_type = db.Column(db.String(50), nullable = False)
    name = db.Column(db.String(50), nullable = False)
    surname = db.Column(db.String(50), nullable = False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    __table_args__ = (UniqueConstraint('name', 'surname', 'last_digits'),)


    def __init__(self, name, surname, pan, last_digits, expiration_month, expiration_year, card_type, user_id):
        self.name = name
        self.surname = surname
        self.pan = pan
        self.last_digits = last_digits
        self.expiration_year = expiration_year
        self.expiration_month = expiration_month
        self.card_type = card_type
        self.user_id = user_id
    @property
    def is_valid(self):
        if not self.pan or not self.last_digits or not self.expiration_month or not self.expiration_year or not self.card_type or not self.name or not self.surname or not self.user_id:
            return False
        return True

class SellerInformation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profit = db.Column(db.Float, nullable = False)
    iban = db.Column(db.String(27), unique = True, nullable = False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    #user = db.relationship('User', backref=db.backref('seller_information', uselist=False), lazy=True)

    def __init__(self, iban, user_id):
        self.profit = 0.0
        self.iban = iban
        self.user_id = user_id
    @property
    def is_valid(self):
        if not self.iban or not self.user_id:
            return False
        return True






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
                category_name = elem['category'] # Ottiene la lista delle categorie dal dizionario prodotto

                # Itera sulle categorie per trovare o creare gli oggetti Category corrispondenti
                category = Category.query.filter_by(name=category_name).first()
                if not category:
                    category = Category.query.filter_by(name='Altro').first()
                

                # Crea e aggiungi il prodotto al database
                prod = Product(
                    name=elem['name'],
                    price=elem['price'],
                    user_id=first_seller.id,
                    description=elem['description'],
                    availability=elem['availability'],
                    category_id=category.id# Aggiunge le categorie al prodotto
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

def add_states():
    states = ['Ordinato', 'Preso in carico', 'Spedito', 'Consegnato']
    for state in states:
        db.session.add(State(name=state))
    db.session.commit()

