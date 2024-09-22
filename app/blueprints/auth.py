from flask import Blueprint, render_template, request, session, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user, current_user
from flask_principal import AnonymousIdentity, Identity, identity_changed
from extensions.database import User, Profile, db
from extensions.princ import anonymous_required
from extensions.limiter import limiter
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, timedelta

app = Blueprint('auth', __name__)

@app.route('/', methods=['GET'])
@anonymous_required
def home():
    return redirect(url_for('shop.shop'))

@app.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    # Per potersi registrare, l'utente non deve essere loggato con alcun account
    if current_user.is_authenticated:
        flash("Sei già loggato", "error")
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
            flash("Il nome utente esiste già", "error")
            return redirect(url_for('auth.login'))
        
        # Password complexity checks
        #if len(password) < 8:
        #    flash('Password must be at least 8 characters long!', category="error")
        #    return redirect(url_for('auth.register'))
        #elif not any(char.isupper() for char in password):
        #    flash('Password must contain at least one uppercase letter!', category="error")
        #    return redirect(url_for('auth.register'))
        #elif not any(char.islower() for char in password):
        #    flash('Password must contain at least one lowercase letter!', category="error")
        #    return redirect(url_for('auth.register'))
        #elif not any(char.isdigit() for char in password):
        #    flash('Password must contain at least one digit!', category="error")
        #    return redirect(url_for('auth.register'))
        # You can add more checks for special characters here (e.g., not any(char in string.punctuation for char in password)
        
        if password != confirm_password:
            flash("Le password non corrispondono", "error")
        else:
            # Creo un nuovo utente, con password cifrata 
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password)
            try:
                db.session.add(new_user)
                db.session.commit()
                db.session.add(Profile(name=name, surname=surname, birth_date=birth_date, user_id=new_user.id))
                db.session.commit()
                flash("Registrazione completata", "success")
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                print(f"Error occurred: {e}")  # Log per il debugging
                flash("Si è verificato un errore durante la registrazione", "error")
                return redirect(url_for('auth.register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per hour", methods=["POST"])  # Limita le richieste POST a 5 all'ora (no bruteforce)
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
                print('login')
                login_user(user, True, timedelta(minutes=5))
                # Avvisa che l'identita dell'utente è cambiata(si passa da anonimo a un nuovo user.id)
                print('invio segnale identity changed')
                print(identity_changed.send(current_app._get_current_object(), identity=Identity(user.id)))
                print(Identity(user.id))
                flash("Accesso effettuato con successo", "success")
                return redirect(url_for('profile.select'))
            else:
                flash("Password errata", "error")
        else:
            flash("Il nome utente non esiste", "error")
            
    return render_template('login.html')

@app.route('/logout', methods=['GET'])
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
    flash("Disconnessione riuscita con successo", "success")
    return redirect(url_for('auth.home'))