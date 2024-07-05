from datetime import timedelta
from flask import Flask, render_template, session, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user, current_user
from flask_principal import Principal, Permission, RoleNeed, Identity, AnonymousIdentity, identity_changed, identity_loaded

from werkzeug.security import generate_password_hash, check_password_hash
# Importa le sessione server-side
from flask_session import Session

# Necessario per rendere thread-safe la variabile globale logged_in_users
import threading


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

login_manager = LoginManager()
login_manager.init_app(app)

# Principals setup
principals = Principal(app)

# Define role-based permissions
admin_permission = Permission(RoleNeed('admin'))
seller_permission = Permission(RoleNeed('seller'))
buyer_permission = Permission(RoleNeed('buyer'))

# variabile globale che segna tutti gli utenti loggati nel database in quel momento
logged_in_users = set()
lock = threading.Lock()


class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(20), nullable = False)
        password = db.Column(db.String(80), nullable = False)

        def __init__(self, username, password):
                self.username = username
                self.password = password
class Profiles(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(20), nullable = False)
        name = db.Column(db.String(20), nullable = False)
        surname = db.Column(db.String(20), nullable = False)
        email = db.Column(db.String(20), nullable = False)
        address = db.Column(db.String(20), nullable = False)
        

        #roles = db.relationship("Role", secondary="user_roles", back_populates="users")
        #def has_role(self, role):
        #       return bool(
        #              Role.query.join(Role.users)
        #              .filter(User.id == self.id)
        #              .filter(Role.slug == role)
        #              .count() == 1
        #       )



class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __init__(self, name, price):
        self.name = name
        self.price = price


#class Role(db.Model):
#       id = db.Column(db.Integer, primary_key=True)
#       name = db.Column(db.String(50), nullable=False)
#       slug = db.Column(db.String(50), nullable=False, unique = True)
#       user = db.relationship("User", secondary = "user_roles", back_populates = "roles")
#
#class UserRole(db.Model):
#       user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
#       role_id = db.Column(db.Integer, db.ForeignKey('role.id'), primary_key=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
        return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
        if request.method == 'POST':
                username = request.form['email']
                password = request.form['password']
                # Cerca una corrispondenza all'interno del database(se esiste, deve essere unica, quindi possiamo usare first())
                user = User.query.filter_by(username=username).first()
                if user:
                        if check_password_hash(user.password, password):
                                # Inizializza la sessione
                                login_user(user)
                                # Avvisa che l'identita dell'utente è cambiata(si passa da anonimo a un nuovo user.id)
                                identity_changed.send(app, identity=Identity(user.id))
                                # Sezione critica con lock; aggiungo l'utente alla lista di utenti attualmente loggati
                                with lock:
                                        logged_in_users.add(username)
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

@app.route('/info')
#@admin_permission.require(http_exception=403)
#@login_required
def info():
        # Ricaviamo tutti gli utenti della tabella User e tutti i prodotti di Products
        all_users = User.query.all()
        all_products = Products.query.all()
        return render_template('info.html', users=all_users, products = all_products, session_usernames = logged_in_users)

@app.route('/shop')
#@login_required
def shop():
        # E' possibile accedere allo shop solo se autenticati(al posto di @login_required)
        if not current_user.is_authenticated:
                flash('You are not logged in. Please log in to enter the shop.', 'error')
                return redirect(url_for('login'))
        products = Products.query.all()
        return render_template('shop.html', products=products)

@app.route('/logout')
@login_required
def logout():
        # Tolgo l'utente dalla lista degli utenti loggati
        with lock:
                logged_in_users.remove(current_user.username)
        # Termino la sessione
        logout_user()
        flash('Logout successful!', category='success')
        return redirect(url_for('home'))

if __name__ == '__main__':
        #with app.app_context():
                #db.create_all()  # Creazione delle tabelle nel database
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
                #User(username='giovanna10@gmail.com', password=generate_password_hash('gg10', method='pbkdf2:sha256'))
                #]
                ## Aggiungi i prodotti al database
                #db.session.add_all(example_users)
                #db.session.commit()
        app.run(debug = True)