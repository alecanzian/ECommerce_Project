from datetime import timedelta
from functools import wraps
from flask import Flask, render_template, session, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user, current_user
from flask_principal import Principal, Permission, RoleNeed, UserNeed, Identity, AnonymousIdentity, identity_changed, identity_loaded, PermissionDenied

from werkzeug.security import generate_password_hash, check_password_hash
# Importa le sessione server-side
from flask_session import Session




# Configurazione del databse
db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/utente/Desktop/UNIVE/vsc/BD/dbms.db'
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

# Definizione della classe User
class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(20), nullable = False)
        password = db.Column(db.String(80), nullable = False)
        roles = db.relationship('Role', secondary=user_roles, backref='users')

        def __init__(self, username, password):
                self.username = username
                self.password = password
                # Aggiunge il ruolo 'buyer' di default
                buyer_role = Role.query.filter_by(name='buyer').first()
                if buyer_role:
                        self.roles.append(buyer_role)
        def has_role(self, role_name):
                return any(role.name == role_name for role in self.roles)

# Definizione della classe Role
class Role(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(50), unique=True, nullable=False)  

        def __init__(self, name):
                self.name = name

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

#class Profiles(db.Model):
#        id = db.Column(db.Integer, primary_key=True)
#        username = db.Column(db.String(20), nullable = False)
#        name = db.Column(db.String(20), nullable = False)
#        surname = db.Column(db.String(20), nullable = False)
#        email = db.Column(db.String(20), nullable = False)
#        address = db.Column(db.String(20), nullable = False)


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



class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

    def __init__(self, name, price):
        self.name = name
        self.price = price
        self.image_url = 'https://img.freepik.com/vettori-premium/un-disegno-di-una-scarpa-con-sopra-la-parola-scarpa_410516-82664.jpg'


# Serve a ricaricare l'oggetto utente usando lo user.id. Usato internamente da Flask-Login
@login_manager.user_loader
def load_user(user_id):
        return User.query.get(int(user_id))



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
                        new_user = User(username=username, password=hashed_password)
                        try:
                                db.session.add(new_user)
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

@app.route('/info')
@login_required
#@admin_permission.require(http_exception=403)
@admin_required
def info():
        # Ricaviamo tutti gli utenti della tabella User, tutti i prodotti di Products e tutti i Ruoli
        all_users = User.query.all()
        all_products = Products.query.all()
        all_roles = Role.query.all()
        return render_template('info.html', users=all_users, products = all_products, roles = all_roles, session_user = current_user) # Passo anche lo username dell'utente loggato(sarà sempre unico)

@app.route('/shop')
@login_required
def shop():
        # E' possibile accedere allo shop solo se autenticati(al posto di @login_required)
        #if not current_user.is_authenticated:
        #        flash('You are not logged in. Please log in to enter the shop.', 'error')
        #        return redirect(url_for('login'))
        products = Products.query.all()
        is_admin = admin_permission.can()
        # Aggiungi log per il debug
        #print(f"User: {current_user.username}, Roles: {[role.name for role in current_user.roles]}")
        #print(f"is_admin: {is_admin}")
        return render_template('shop.html', products=products, enter = is_admin)

@app.route('/logout')
@login_required
def logout():
        # Termino la sessione
        logout_user()
        # Remove session keys set by Flask-Principal
        # Dato che la sessione è un dizionario, dopo il login, Flask-Principal crea anche due chiavi: identity.name, identity.auth_type. QUindi finita la sessione, eliminiamo anche i valore associato a queste due chiavi
        for key in ('identity.name', 'identity.auth_type'):
                session.pop(key, None)

        # Tell Flask-Principal the user is anonymous
        identity_changed.send(app,identity=AnonymousIdentity())
        flash('Logout successful!', category='success')
        return redirect(url_for('home'))

@app.route('/product/<int:product_id>')
@login_required
def access_product(product_id):
        product = Products.query.get_or_404(product_id)
        return render_template('product.html', product=product)

if __name__ == '__main__':
        with app.app_context():
                db.create_all()  # Creazione delle tabelle nel database
                #add_roles()  # Popola il database con ruoli di esempio
                #example_products = [
                #Products(name='Scarpe Nike', price=10.99),
                #Products(name='Jeans Levis', price=19.99),
                #Products(name='Occhiali da sole H. Boss', price=15.49)
                #]
                ## Aggiungi i prodotti al database
                #db.session.add_all(example_products)
                #db.session.commit()
                #example_users = [
                #User(username='alessandrocanzian2003@gmail.com', password=generate_password_hash('alex', method='pbkdf2:sha256')),
                #User(username='paoletto66@gmail.com', password=generate_password_hash('pp66', method='pbkdf2:sha256')),
                #User(username='giovanna10@gmail.com', password=generate_password_hash('gg10', method='pbkdf2:sha256')),
                #User(username='irene@gmail.com', password=generate_password_hash('irene', method='pbkdf2:sha256'))
                #]
                ## Aggiungi i prodotti al database
                #db.session.add_all(example_users)
                #db.session.commit()
                #set_user_with_role('alessandrocanzian2003@gmail.com', 'admin')  # Aggiungi un utente di esempio
                #set_user_with_role('alessandrocanzian2003@gmail.com', 'buyer')  # Aggiungi un utente di esempio
                #set_user_with_role('paoletto66@gmail.com', 'buyer')  # Aggiungi un utente di esempio
                #set_user_with_role('giovanna10@gmail.com', 'buyer')  # Aggiungi un utente di esempio
                #set_user_with_role('irene@gmail.com', 'buyer')  # Aggiungi un utente di esempio
        app.run(debug = True)
 