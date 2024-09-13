from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from flask_principal import AnonymousIdentity, Identity, identity_changed
from extensions.database import User, Profile, db
from extensions.princ import anonymous_required
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, timedelta

app = Blueprint('auth', __name__)

@app.route('/')
@anonymous_required
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    # Per potersi registrare, l'utente non deve essere loggato con alcun account
    if current_user.is_authenticated:
        flash('You are already logged in. Please log out to register a new account.', 'error')
        return redirect(url_for('shop.shop'))
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
            return redirect(url_for('auth.login'))

        if password != confirm_password:
            flash('Passwords do not match!', category='error')
        else:
            # Creo un nuovo utente, con password cifrata 
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password)
            try:
                db.session.add(new_user)
                db.session.commit()
                db.session.add(Profile(name=name, surname=surname, birth_date=birth_date, user_id=new_user.id))
                db.session.commit()
                flash('Registration successful!', category='success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                print(f"Error occurred: {e}")  # Log per il debugging
                flash('An error occurred during registration. Please try again.', category='error')
                return redirect(url_for('auth.register'))
    return render_template('register.html')

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
                identity_changed.send(app, identity=Identity(current_user.id))
                flash('Login successful!', category='success')
                return redirect(url_for('profile.profile_selection'))
            else:
                flash('Incorrect password.', category='error')
        else:
            flash('Login failed. Check your email and password.', category='error')
    return render_template('login.html')

@app.route('/logout')
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
    session.pop('current_profile_id', None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(app,identity=AnonymousIdentity())
    flash('Logout successful!', 'success')
    return redirect(url_for('auth.home'))