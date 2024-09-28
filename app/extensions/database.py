from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from werkzeug.security import generate_password_hash
from datetime import datetime

db = SQLAlchemy()

# Tabella di associazione per la relazione molti-a-molti tra utenti e ruoli
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)
    
# Definizione della classe User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique = True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

    roles = db.relationship('Role', secondary=user_roles, lazy = True)

    profiles = db.relationship('Profile', backref='user', lazy=True)#?
    products = db.relationship('Product', backref='user', lazy = True)
    addresses = db.relationship('Address', lazy=True,)
    orders = db.relationship('Order', backref = 'user', lazy = True)
    cards = db.relationship('Card', lazy = True)
    seller_information = db.relationship('SellerInformation', uselist=False, lazy=True)


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
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    image_url = db.Column(db.String(256), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    cart_items = db.relationship('Cart', lazy=True)

    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='unique_profile'),
    )
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
    postal_code = db.Column(db.String(5), nullable=False)
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
    name = db.Column(db.String(50),nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(256), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    availability = db.Column(db.Integer, nullable = False)

    #profile_id = db.Column(db.Integer, db.ForeignKey('profile.id', ondelete = 'SET NULL'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False) 

    #categories = db.relationship('Category', secondary=product_categories, backref='products')

    in_carts = db.relationship('Cart', backref='product', lazy = True)

    in_order = db.relationship('OrderProduct', backref = 'product', lazy = True)

    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='unique_product_seller'),
    )

    def __init__(self, name, price, user_id, description, category_id, image_url = 'https://img.freepik.com/vettori-premium/un-disegno-di-una-scarpa-con-sopra-la-parola-scarpa_410516-82664.jpg', availability = 1):
        self.name = name
        self.price = price
        # Riconosce se una stringa è solo piena di spazi
        if image_url.isspace():
            self.image_url = 'https://img.freepik.com/vettori-premium/un-disegno-di-una-scarpa-con-sopra-la-parola-scarpa_410516-82664.jpg'
        else:
            self.image_url = image_url
        self.description = description
        self.availability = availability
        self.user_id = user_id
        self.category_id = category_id
    @property
    def is_valid(self):
        if not self.name or not self.image_url or not self.description or not self.user_id or not self.category_id:
            return False
        return True

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable = False)

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable = False)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable = False)

    __table_args__ = (db.UniqueConstraint('product_id', 'profile_id', name='unique_product_profile'),)

    def __init__(self, quantity, product_id, profile_id):
        self.quantity = quantity
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
    address = db.Column(db.String(256),nullable = False)
    card_last_digits = db.Column(db.String(4),nullable = False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relazione con i prodotti attraverso tabella intermedia OrderProduct
    products = db.relationship('OrderProduct', backref='order', lazy = True)

    def __init__(self, user_id, address, card_last_digits,total_price = 0.0):
        self.user_id = user_id
        self.total_price = total_price
        self.address = address
        self.card_last_digits = card_last_digits
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
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable = False)

    notification = db.relationship('Notification', backref='order_product', lazy = True)


    def __init__(self, order_id, product_id, product_name, quantity, seller_id):
        self.order_id = order_id
        self.product_id = product_id
        self.product_name = product_name
        self.quantity = quantity
        self.seller_id = seller_id
        self.state = State.query.filter_by(name = 'Ordinato').first()
    @property
    def is_valid(self):
        if not self.quantity or not self.product_name or not self.seller_id or not self.order_id or not self.state_id:
            return False
        return True

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    products = db.relationship('Product', backref='category', lazy = True)

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

    order_product = db.relationship('OrderProduct', backref = 'state', lazy = True)
    def __init__(self, name):
        self.name = name
    @property
    def is_valid(self):
        if not self.name:
            return False
        return True
        
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_product_id = db.Column(db.Integer, db.ForeignKey('order_product.id'), nullable=False)
    
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

    def __init__(self,sender_id, receiver_id,type, order_product_id):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.type = type
        self.order_product_id = order_product_id
    @property
    def is_valid(self):
        if not self.type or not self.timestamp or not self.sender_id or not self.receiver_id or not self.order_product_id:
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

    __table_args__ = (UniqueConstraint('name', 'surname', 'last_digits', 'user_id', name = 'unique_card'),)


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
            
# Funzione per popolare la tabella State
def add_states():
    states = ['Ordinato', 'Preso in carico', 'Spedito', 'Consegnato']
    for state_name in states:
        state = State.query.filter_by(name=state_name).first()
        if not state:
            db.session.add(State(name=state_name))
            db.session.commit()
            
# Funzione per popolare la tabella Category
def add_categories():
    categories_list = [
        'Abbigliamento e accessori',
        'Alimentari e cura della casa',
        'Auto e moto',
        'Arte',
        'Cancelleria e prodotti per ufficio',
        'Casa e cucina',
        'Musica',
        'Elettronica',
        'Fai da te',
        'Film e TV',
        'Giardino e giardinaggio',
        'Giochi e giocattoli',
        'Grandi elettrodomestici',
        'Illuminazione',
        'Informatica',
        'Libri',
        'Prima infanzia',
        'Prodotti per animali domestici',
        'Salute e bellezza',
        'Sport e tempo libero',
        'Valigie e accessori da viaggio',
        'Videogiochi'
    ]
            
    for category_name in categories_list:
        category = Category.query.filter_by(name=category_name).first()
        # Controlla se la categoria esiste già nel database
        if not category:
            # Se la categoria non esiste, aggiungila
            db.session.add(Category(name=category_name))
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
                if category:    
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

def popolate_db():
    db.drop_all() # Elimina tutte le tabelle nel database
    db.create_all()  # Crea tutte le tabelle nel database
    add_roles()  # Popola il database con ruoli di esempio
    add_states()
    add_categories()
    
    # Viene inserito il primo utente (admin) con password admin (default)
    user = User(username = 'admin@admin.com', password = generate_password_hash('admin', method='pbkdf2:sha256') )
    db.session.add(user)
    db.session.flush()
    db.session.add(Profile(name = 'Admin', surname = 'Admin', birth_date=datetime.strptime('1990-01-01', '%Y-%m-%d').date(), user_id=user.id))
    db.session.commit()
    
    set_user_with_role(user, 'admin')  # Aggiungi un utente di esempio
    set_user_with_role(user, 'buyer')  # Aggiungi un utente di esempio
    
    # Vanno eliminati
    
    db.session.add(SellerInformation(iban='IT93N0300203280241424179211', user_id=user.id))
    db.session.commit()
    
    set_user_with_role(user, 'seller')
    
    example = User(username = 'canzianpaolo@gmail.com', password = generate_password_hash('paolo', method='pbkdf2:sha256') )
    db.session.add(example)
    db.session.commit()
    
    db.session.add(Profile(name = 'Paolo', surname = 'Canzian', birth_date=datetime.strptime('1966-05-11', '%Y-%m-%d').date(), user_id=example.id))
    db.session.commit()
    
    addr2 = Address(street = 'Via borgo san andrea 85', postal_code = 31050, city = 'Povegliano', province = 'TV', country = 'Italia', user_id = example.id)
    db.session.add(addr2)
    db.session.commit()
    
    card1 = Card( name = 'alessandro', surname = 'canzian', pan= '1234567890987890', last_digits = '7890', expiration_month = '11', expiration_year= '2024', card_type = 'credit', user_id = example.id)
    db.session.add(card1)
    db.session.commit()
    
    card1 = Card( name = 'paolo', surname = 'canzian', pan= '1872567890981234', last_digits = '1234', expiration_month = '12', expiration_year= '2032', card_type = 'credit', user_id = user.id)
    db.session.add(card1)
    db.session.commit()
        
    example_products = [
        {"name": "Scarpe Nike", "price": 10.99, "description": "gnegne", "availability": 10, "category": "Abbigliamento e accessori"},
        {"name": "Jeans Levis", "price": 19.99, "description": "gnegne", "availability": 2, "category": "Abbigliamento e accessori"},
        {"name": "Occhiali da sole H. Boss", "price": 15.49, "description": "gnegne", "availability": 5, "category": "Salute e bellezza"},
        {"name": "Laptop Dell", "price": 499.99, "description": "Laptop ad alte prestazioni", "availability": 3, "category": "Elettronica"},
        {"name": "Smartphone Samsung", "price": 299.99, "description": "Smartphone di ultima generazione", "availability": 15, "category": "Elettronica"},
        {"name": "Divano Ikea", "price": 199.99, "description": "Divano confortevole e moderno", "availability": 4, "category": "Casa e cucina"},
        {"name": "Trapano Bosch", "price": 89.99, "description": "Trapano per lavori di fai da te", "availability": 12, "category": "Fai da te"},
        {"name": "Romanzo di Dan Brown", "price": 12.99, "description": "Thriller avvincente", "availability": 20, "category": "Libri"},
        {"name": "Chitarra Fender", "price": 249.99, "description": "Chitarra elettrica per musicisti", "availability": 2, "category": "Musica"},
        {"name": "Orologio Rolex", "price": 4999.99, "description": "Orologio di lusso", "availability": 1, "category": "Abbigliamento e accessori"},
        {"name": "Videogioco PS5", "price": 59.99, "description": "Videogioco di ultima generazione", "availability": 30, "category": "Giochi e giocattoli"},
        {"name": "Cibo per cani", "price": 24.99, "description": "Alimento completo per cani", "availability": 50, "category": "Prodotti per animali domestici"},
        {"name": "Set di pentole", "price": 79.99, "description": "Set di pentole antiaderenti", "availability": 10, "category": "Casa e cucina"}
    ]
    
    add_products(example_products)
