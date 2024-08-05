from datetime import date, datetime, timedelta
from functools import wraps
from flask import Flask, render_template, session, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, text
from flask_login import UserMixin, LoginManager, fresh_login_required, login_required, login_user, logout_user, current_user
from flask_principal import Principal, Permission, RoleNeed, UserNeed, Identity, AnonymousIdentity, identity_changed, identity_loaded, PermissionDenied
from werkzeug.security import generate_password_hash, check_password_hash
# Importa le sessione server-side
from flask_session import Session
import os

# Configurazione del database
db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecretkey'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'dbms.db')
db = SQLAlchemy(app)

# Configurazione per la sessione server-side
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=40)  # Imposta la durata della sessione a 20 minuti
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = db
# Inizializzazione dell'oggetto sess e associazione di sess all'applicazione
sess = Session(app)
#sess.init_app(app)

# Inizializzazione del login_manager e associazione dell'oggetto all'applicazione
login_manager = LoginManager()
login_manager.init_app(app)

# Settaggio del login_manager. Quando un utente anonimo accede a una ruote col decoratore @login_required, allora viene rimandato alla schermata di login_view con il messaggio login_message
login_manager.login_view = "login"
login_manager.login_message = "To access, you have to log in."
login_manager.login_message_category = "info"

# Settaggio del login_manager. Quando un utente anonimo accede a una ruote col decoratore @login_required, allora viene rimandato alla schermata di refresh_view con il messaggio login_message
login_manager.refresh_view = "login"
login_manager.needs_refresh_message = "To protect your account, please reauthenticate to access this page."
login_manager.needs_refresh_message_category = "info"

# Principals setup
principals = Principal(app)

# Define role-based permissions
admin_permission = Permission(RoleNeed('admin'))
seller_permission = Permission(RoleNeed('seller'))
buyer_permission = Permission(RoleNeed('buyer'))

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
        name = db.Column(db.String(30), nullable = False)
        surname = db.Column(db.String(30), nullable = False)
        birth_date = db.Column(db.Date, nullable = False)
        username = db.Column(db.String(20), nullable = False)
        password = db.Column(db.String(80), nullable = False)

        roles = db.relationship('Role', secondary=user_roles, backref='users')
        profiles = db.relationship('Profile', backref='user')

        def __init__(self, name, surname,birth_date, username, password):
                self.name = name
                self.surname = surname
                self.username = username
                self.password = password
                self.birth_date = birth_date

                # Aggiunge il ruolo 'buyer' di default
                buyer_role = Role.query.filter_by(name='buyer').first()
                if buyer_role:
                        self.roles.append(buyer_role)

        def has_role(self, role_name):
                return any(role.name == role_name for role in self.roles)

class Profile(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(20), nullable = False)
        surname = db.Column(db.String(20), nullable = False)
        image_url = db.Column(db.String(255), nullable=False)
        #address = db.Column(db.String(20), nullable = False)

        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

        products = db.relationship('Product', backref='profile')

        def __init__(self, name, surname, user_id, image_url = 'https://static.vecteezy.com/ti/vettori-gratis/p1/2318271-icona-profilo-utente-vettoriale.jpg'):
                self.name = name
                self.surname = surname
                self.image_url = image_url
                self.user_id = user_id

class Product(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(50), nullable=False)
        price = db.Column(db.Float, nullable=False)
        image_url = db.Column(db.String(255), nullable=False)
        description = db.Column(db.String(255), nullable=False)
        availability = db.Column(db.Integer, nullable = False)



        profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False) 
        categories = db.relationship('Category', secondary=product_categories, backref='products')




        def __init__(self, name, price, profile_id, description, categories, availability = 1, image_url = 'https://img.freepik.com/vettori-premium/un-disegno-di-una-scarpa-con-sopra-la-parola-scarpa_410516-82664.jpg'):
                profile = db.session.get(Profile, int(profile_id))
                if not profile or not profile.user.has_role('seller'):
                        raise ValueError("Il profilo non appartiene a un utente con il ruolo di seller.")
                self.name = name
                self.price = price
                self.image_url = image_url
                self.description = description
                self.availability = availability
                self.profile_id = profile_id
                for c in categories:
                    #existing_category = Category.query.filter_by(name=c).first()
                    #if existing_category:
                    #    # Se la categoria esiste, aggiungila al prodotto
                    #    self.categories.append(existing_category)
                    #else:
                    #    # Se la categoria non esiste, crea una nuova istanza di Category e aggiungila al prodotto
                    #    altro_category = Category.query.filter_by(name='Altro').first()
                    self.categories.append(c)

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

# The Identity represents the user, and is stored/loaded from various locations (eg session) for each request. The Identity is the user’s avatar to the system. It contains the access rights that the user has.
# A Need is the smallest grain of access control, and represents a specific parameter for the situation.Whilst a Need is a permission to access a resource, an Identity should provide a set of Needs that it has access to.
# A Permission is a set of requirements, any of which should be present for access to a resource.
@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))

# Serve a ricaricare l'oggetto utente usando lo user.id. Usato internamente da Flask-Login
@login_manager.user_loader
def load_user(user_id):
        return db.session.get(User,int(user_id)) #User.query.get(int(user_id)) è considerato legacy

# Decoratore personalizzato per gestire il caso in cui l'utente non ha l'autorizzazione(ovvero non possiede il ruolo) per eseguire una azione
def anonymous_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            flash('Devi prima eseguire il log out', category = 'error')
            return redirect(url_for('shop'))  # Redirige alla home se l'utente è loggato
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@anonymous_required
def home():
        return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
        if request.method == 'POST':
                username = request.form['email']
                password = request.form['password']
                # Cerca una corrispondenza all'interno del database(se esiste, deve essere unica, quindi possiamo usare first())
                user = User.query.filter_by(username=username).first()
                if user:
                        if check_password_hash(user.password, password):
                                # Inizializza la sessione, remeber me = True, REMEMBER_COOKIE_DURATION  = 5 minuti
                                """
                                By default, when the user closes their browser the Flask Session is deleted and the user is logged out. “Remember Me” prevents the user from accidentally being logged out when they close their browser. This does NOT mean remembering or pre-filling the user’s username or password in a login form after the user has logged out.
                                Thanks to Flask-Login, just pass remember=True to the login_user call. A cookie will be saved on the user’s computer, and then Flask-Login will automatically restore the user ID from that cookie if it is not in the session. The amount of time before the cookie expires can be set with the REMEMBER_COOKIE_DURATION configuration or it can be passed to login_user. The cookie is tamper-proof, so if the user tampers with it (i.e. inserts someone else’s user ID in place of their own), the cookie will merely be rejected, as if it was not there.
                                """
                                login_user(user, True, timedelta(minutes=5))
                                # Avvisa che l'identita dell'utente è cambiata(si passa da anonimo a un nuovo user.id)
                                identity_changed.send(app, identity=Identity(user.id))
                                flash('Login successful!', category='success')
                                return redirect(url_for('shop'))
                        else:
                                flash('Incorrect password.', category='error')
                else:
                        flash('Login failed. Check your email and password.', category='error')
        return render_template('login.html') 

@app.route('/register', methods=['GET', 'POST'])
def register():
        # Per potersi registrare, l'utente non deve essere loggato con alcun account
        if current_user.is_authenticated:
                flash('You are already logged in. Please log out to register a new account.', 'error')
                return redirect(url_for('shop'))
        if request.method == 'POST':
                name = request.form['name']
                surname = request.form['surname']
                birth_date = date.fromisoformat(request.form['birth_date'])  # Assumendo il formato 'YYYY-MM-DD'
                username = request.form['email']
                password = request.form['password']
                confirm_password = request.form['confirm_password']

                # Controllo se l'username esiste già
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                        flash('Username already exists. Please login.', category='error')
                        return redirect(url_for('login'))

                if password != confirm_password:
                        flash('Passwords do not match!', category='error')
                else:
                        # Creo un nuovo utente, con password cifrata 
                        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                        new_user = User(name = name, surname = surname, birth_date = birth_date,  username=username, password=hashed_password)
                        try:
                                db.session.add(new_user)
                                db.session.commit()
                                db.session.add(Profile(name = new_user.name, surname = new_user.surname, user_id=new_user.id))
                                db.session.commit()
                                flash('Registration successful!', category='success')
                                return redirect(url_for('login'))
                        except Exception as e:
                                db.session.rollback()
                                print(f"Error occurred: {e}")  # Log per il debugging
                                flash('An error occurred during registration. Please try again.', category='error')
                                return redirect(url_for('register'))
        return render_template('register.html')

# Decoratore personalizzato per gestire il caso in cui l'utente non ha l'autorizzazione di admin(ovvero non possiede il ruolo admin) per accedere a info.html
# Avrei potuto utilizzare @admin_permission.require() al posto del decoratore personalizzato, tuttavia così non posso gestire l'errore
# Avrei anche potuto creare un try all'interno della funzione(come ho fatto nella funzione del decoratore), però ho preferito mantenere il codice pulito
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Importa il permesso admin direttamente qui per evitare cicli di importazione
        from app import admin_permission  
        try:
            admin_permission.test()
        except PermissionDenied:
            flash('You do not have permission to access this page.', 'error')
            # Reindirizza alla pagina dello shop se l'utente non è admin
            return redirect(url_for('shop'))  
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Importa il permesso admin direttamente qui per evitare cicli di importazione
        from app import seller_permission 
        try:
            seller_permission.test()
        except PermissionDenied:
            flash('You do not have permission to access this page.', 'error')
            # Reindirizza alla pagina dello shop se l'utente non è admin
            return redirect(url_for('shop'))  
        return f(*args, **kwargs)
    return decorated_function

def buyer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Importa il permesso admin direttamente qui per evitare cicli di importazione
        from app import buyer_permission  
        try:
            buyer_permission.test()
        except PermissionDenied:
            flash('You do not have permission to access this page.', 'error')
            # Reindirizza alla pagina dello shop se l'utente non è admin
            return redirect(url_for('shop'))  
        return f(*args, **kwargs)
    return decorated_function

@app.route('/info')
@login_required
@admin_required
def info():
        # Ricaviamo tutti gli utenti della tabella User, tutti i prodotti di Products e tutti i Ruoli
        all_users = User.query.all()
        all_products = Product.query.all()
        all_roles = Role.query.all()
        all_categories = Category.query.all()
        return render_template('info.html', users=all_users, products = all_products, roles = all_roles, categories = all_categories, session_user = current_user) # Passo anche lo username dell'utente loggato(sarà sempre unico)

@app.route('/shop')
@login_required
def shop():
        # Inizializzazione di tutte le chiavi necessarie
        # Visto che ci sono tre controlli, ovvero la barra di ricerca, il checkbox e il range di prezzo, ho bisogno di salvarmi ciò che visualizza l'utente.
        if 'selected_products' not in session:
            session['selected_products'] = [p.id for p in Product.query.all()]
        if 'selected_categories' not in session:
            session['selected_categories'] = []
        if 'min_price' not in session:
            session['min_price'] = 0.0
        if 'max_price' not in session:
            session['max_price'] = 6000.0
        
        # I prodotti il cui id è presente nella sessione. Questo perchè potrebbe esserci una route che reindirizza a shop e session['selected_products'] potrebbe averedegli elementi
        products = Product.query.filter(Product.id.in_(session['selected_products'])).all()

        return render_template('shop.html', products=products, categories = Category.query.all()) 

@app.route('/logout')
@login_required
def logout():
        # Termino la sessione
        logout_user()
        # Remove session keys set by Flask-Principal
        # Dato che la sessione è un dizionario, dopo il login, Flask-Principal crea anche due chiavi: identity.name, identity.auth_type. QUindi finita la sessione, eliminiamo anche i valore associato a queste due chiavi
        for key in ('identity.name', 'identity.auth_type'):
                session.pop(key, None)

        # Rimuovo tutte le chiavi utilizzate per il filtro dei prodotti
        session.pop('selected_products', None)
        session.pop('selected_categories', None)
        session.pop('min_price',None)
        session.pop('max_price',None)

        # Tell Flask-Principal the user is anonymous
        identity_changed.send(app,identity=AnonymousIdentity())
        flash('Logout successful!', category='success')
        return redirect(url_for('home'))

@app.route('/product/<int:product_id>')
@login_required
def access_product(product_id):
        product = Product.query.get_or_404(product_id)
        return render_template('product.html', product=product)

@app.route('/profile')
@login_required
@fresh_login_required
#@buyer_required
def profile():    
    return render_template('profile.html')

@app.route('/cart')
@login_required
@buyer_required
def cart():
    return render_template('cart.html')

@app.route('/filtered_results', methods=['POST'])
@login_required
def filtered_results():
    if request.method == 'POST':
        # Estrapolo tutte le informazioni necessarie dal form
        query = request.form.get('query', '') # query della barra di ricerca
        selected_categories = request.form.getlist('selected_categories') # lista delle categorie selezionate
        min_price = float(request.form.get('minPriceRange', 0)) # prezzo minimo
        max_price = float(request.form.get('maxPriceRange', 6000)) # prezzo massimo

        # Aggiorno i valori corrispondenti alle chiavi 
        session['min_price'] = min_price
        session['max_price'] = max_price
        session['selected_categories'] = selected_categories
        

        # Filtra i prodotti in base ai criteri
        products = Product.query

        # Se la query non è una stringa vuota
        if query:
            products = products.filter(Product.name.ilike(f'%{query}%'))

        # Se ci sono delle categorie selezionate
        if selected_categories:
            products = products.filter(Product.categories.any(Category.name.in_(selected_categories)))

        # I prodotti che rispettano che corrispondono a quelli precedenti e filtrati in base al prezzo
        products = products.filter(Product.price >= min_price, Product.price <= max_price).all()

        # Aggiorno gli id dei prodotti
        session['selected_products'] = [p.id for p in products]


        return render_template('shop.html', products=products, categories=Category.query.all())

@app.route('/reset_filters', methods=['POST'])
@login_required
@buyer_required
def reset_filters():
    if request.method == 'POST':
        # Rimuovi tutte le categorie selezionate dalla sessione
        session['selected_categories'] = []

        # Reimposta i valori di min_price e max_price nella sessione
        session['min_price'] = 0.0
        session['max_price'] = 6000.0

        # Reimposta i prodotti visibili utilizzando i filtri di default
        products = Product.query.all()

        # Aggiorna la sessione con gli ID dei prodotti visibili
        session['selected_products'] = [p.id for p in products]

        # Ritorna alla pagina shop con i prodotti e categorie aggiornati
        return redirect(url_for('shop'))

# PARTE AGGIUNTIVA(ancora da fare)

@app.route('/create_product', methods=['POST'])
@seller_required
def create_product():
    name = request.form.get('name')
    price = request.form.get('price')
    profile_id = request.form.get('profile_id')

    # Verifica se il profilo appartiene all'utente corrente
    profile = Profile.query.get(profile_id)
    if profile.user_id != current_user.id:
        return "Non hai il permesso di utilizzare questo profilo", 403

    new_product = Product(name=name, price=price, profile_id=profile_id)
    db.session.add(new_product)
    db.session.commit()
    return "Prodotto creato con successo", 201

@app.route('/save_profile', methods=['POST'])
@login_required
@fresh_login_required
@buyer_required
def save_profile():
    username = request.form.get('username')
    
    # Verifica che il nuovo username non sia vuoto
    if username:
        # Esegui ulteriori controlli, come assicurarsi che l'username non sia già preso
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Username already taken.', 'error')
        else:
            current_user.username = username
            db.session.commit()
            flash('Profile updated successfully!', 'success')
    else:
        flash('Username cannot be empty.', 'error')
    
    return redirect(url_for('profile'))

#________________FUNZIONI PER POPOLARE IL DATABASE______________________________________


# Da chiamare solo quando serve popolare la tabella Role
def add_roles():
        roles = ['admin', 'seller', 'buyer']
        for role_name in roles:
                role = Role.query.filter_by(name=role_name).first()
                if not role:
                        new_role = Role(name=role_name)
                        db.session.add(new_role)
        db.session.commit()

# Dato un utente preesistente, aggiunge il ruolo passato come parametro(nel caso non sia presente in user.roles)
def set_user_with_role(name, role_name):
        user = User.query.filter_by(username=name).first()
        role = Role.query.filter_by(name=role_name).first()
        if user:
                if role:
                       if role not in user.roles:
                                user.roles.append(role)
        db.session.commit()

# Data una lista di utenti, popola la tabella User e  inizializza il profilo di default
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

    # Salva tutte le modifiche nel database
    db.session.commit()


# Data una lista di prodotti, popola la tabella Products e collega i prodotti all'unico profilo collegato allo user che ha ruolo admin
def add_products(products_list):
        admin_user = User.query.filter(User.roles.any(Role.name=='admin')).first()
        if admin_user:
                admin_profile_id = Profile.query.filter_by(user_id=admin_user.id).first().id
                if admin_profile_id:
                        for elem in products_list:
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
                                profile_id=admin_profile_id,
                                description=elem['description'],
                                availability=elem['availability'],
                                categories=category_objects  # Aggiunge le categorie al prodotto
                            )
                            db.session.add(prod)

                        db.session.commit()

# Funzione per popolare la tabella Category
def add_categories(categories_list):
    for nome_categoria in categories_list:
        categoria = Category(name=nome_categoria)
        db.session.add(categoria)
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

if __name__ == '__main__':
        with app.app_context():
                db.create_all()  # Creazione delle tabelle nel database
                #add_roles()  # Popola il database con ruoli di esempio
                #
                #example_users = [
                #{
                #        'name': 'Alessandro', 
                #        'surname': 'Canzian', 
                #        'birth_date': '2003-03-30', 
                #        'username': 'alessandrocanzian2003@gmail.com', 
                #        'password': 'alex'
                #},
                #{
                #        'name': 'Paolo', 
                #        'surname': 'Canzian', 
                #        'birth_date': '1966-05-11', 
                #        'username': 'paoletto66@gmail.com', 
                #        'password': 'pp66'
                #},
                #{
                #        'name': 'Giovanna', 
                #        'surname': 'Zanatta', 
                #        'birth_date': '1958-09-21', 
                #        'username': 'giovanna10@gmail.com', 
                #        'password': 'gg10'
                #},
                #{
                #        'name': 'Irene', 
                #        'surname': 'Canzian', 
                #        'birth_date': '2003-04-21', 
                #        'username': 'irene@gmail.com', 
                #        'password': 'irene'
                #}
                #]
                #add_users(example_users)
                #
                #set_user_with_role('alessandrocanzian2003@gmail.com', 'admin')  # Aggiungi un utente di esempio
                #set_user_with_role('alessandrocanzian2003@gmail.com', 'buyer')  # Aggiungi un utente di esempio
                #set_user_with_role('alessandrocanzian2003@gmail.com', 'seller')  # Aggiungi un utente di esempio
                #set_user_with_role('paoletto66@gmail.com', 'buyer')  # Aggiungi un utente di esempio
                #set_user_with_role('giovanna10@gmail.com', 'buyer')  # Aggiungi un utente di esempio
                #set_user_with_role('irene@gmail.com', 'buyer')  # Aggiungi un utente di esempio
                #
                #example_categories = [
                #    'Elettronica',
                #    'Abbigliamento',
                #    'Casa e Giardino',
                #    'Sport e Tempo Libero',
                #    'Giochi e Giocattoli',
                #    'Alimentari',
                #    'Libri e Riviste',
                #    'Salute e Bellezza',
                #    'Arredamento',
                #    'Auto e Moto',
                #    'Fai da te',
                #    'Musica',
                #    'Film e TV',
                #    'Animali domestici',
                #    'Strumenti Musicali',
                #    'Telefonia',
                #    'Arte e Collezionismo',
                #    'Viaggi',
                #    'Tecnologia',
                #    'Orologi e Gioielli',
                #    'Altro'
                #]
                #add_categories(example_categories)
                #
                #example_products = [
                #    {"name": "Scarpe Nike", "price": 10.99, "description": "gnegne", "availability": 10, "categories": ["Sport e Tempo Libero"]},
                #    {"name": "Jeans Levis", "price": 19.99, "description": "gnegne", "availability": 2, "categories": ["Abbigliamento"]},
                #    {"name": "Occhiali da sole H. Boss", "price": 15.49, "description": "gnegne", "availability": 5, "categories": ["Salute e Bellezza", "Abbigliamento"]},
                #    {"name": "Laptop Dell", "price": 499.99, "description": "Laptop ad alte prestazioni", "availability": 3, "categories": ["Elettronica", "Tecnologia"]},
                #    {"name": "Smartphone Samsung", "price": 299.99, "description": "Smartphone di ultima generazione", "availability": 15, "categories": ["Elettronica", "Telefonia"]},
                #    {"name": "Divano Ikea", "price": 199.99, "description": "Divano confortevole e moderno", "availability": 4, "categories": ["Casa e Giardino", "Arredamento"]},
                #    {"name": "Trapano Bosch", "price": 89.99, "description": "Trapano per lavori di fai da te", "availability": 12, "categories": ["Fai da te", "Tecnologia"]},
                #    {"name": "Romanzo di Dan Brown", "price": 12.99, "description": "Thriller avvincente", "availability": 20, "categories": ["Libri e Riviste"]},
                #    {"name": "Chitarra Fender", "price": 249.99, "description": "Chitarra elettrica per musicisti", "availability": 2, "categories": ["Strumenti Musicali", "Musica"]},
                #    {"name": "Orologio Rolex", "price": 4999.99, "description": "Orologio di lusso", "availability": 1, "categories": ["Orologi e Gioielli"]},
                #    {"name": "Videogioco PS5", "price": 59.99, "description": "Videogioco di ultima generazione", "availability": 30, "categories": ["Giochi e Giocattoli", "Tecnologia"]},
                #    {"name": "Cibo per cani", "price": 24.99, "description": "Alimento completo per cani", "availability": 50, "categories": ["Animali domestici", "Alimentari"]},
                #    {"name": "Set di pentole", "price": 79.99, "description": "Set di pentole antiaderenti", "availability": 10, "categories": ["Casa e Giardino", "Altro"]}
                #]
                #add_products(example_products)
            

        app.run(debug = True)
 