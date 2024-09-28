from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user
from flask_principal import AnonymousIdentity, Identity, identity_changed
from extensions.database import User, Profile, db
from extensions.princ import anonymous_required
from extensions.limiter import limiter
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, timedelta

app = Blueprint('auth', __name__)

@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('shop.shop'))

# Gestisce la registrazione del nuovo utente
@app.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        birth_date_str = request.form.get('birth_date')
        username = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Controllo i dati del form
        if not name or not surname or not birth_date_str or not username or not password or not confirm_password:
            flash('Inserisci tutti i campi', 'error')
            return redirect(url_for('auth.register'))

        # Controllo se le password corrispondono
        if password != confirm_password:
            flash("Le password non corrispondono", "error")
            return redirect(url_for('auth.register'))
        
        # Password complexity checks
        if len(password) < 8:
            flash('Password must be at least 8 characters long!', category="error")
            return redirect(url_for('auth.register'))
        elif not any(char.isupper() for char in password):
            flash('Password must contain at least one uppercase letter!', category="error")
            return redirect(url_for('auth.register'))
        elif not any(char.islower() for char in password):
            flash('Password must contain at least one lowercase letter!', category="error")
            return redirect(url_for('auth.register'))
        elif not any(char.isdigit() for char in password):
            flash('Password must contain at least one digit!', category="error")
            return redirect(url_for('auth.register'))
        

        
        try:
            # Ottieni la data corrente
            current_date = date.today()
            # Definisci l'intervallo massimo per la data di nascita (100 anni fa)
            earliest_date = date(current_date.year - 100, 1, 1)
            # Controllo della data di nascita
            birth_date = date.fromisoformat(birth_date_str)

            # Controlla se la data è nel futuro
            if birth_date > current_date:
                flash("La data di nascita non può essere nel futuro.")
                return redirect(url_for('auth.register'))

            # Controlla se la data è troppo indietro (più di 100 anni fa)
            if birth_date < earliest_date:
                flash(f"L'anno di nascita deve essere compreso tra {earliest_date.year} e {current_date.year}.")
                return redirect(url_for('auth.register'))
            
            # Genero la password codificata e creo l'utente
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            # Creo la chiave id necessaria per la creazione del profilo
            db.session.flush()

            # Genero il profilo associato
            db.session.add(Profile(name=name, surname=surname, birth_date=birth_date, user_id=new_user.id))
            db.session.commit()
        
        except IntegrityError:
            db.session.rollback()
            flash('Username già esistente', 'error')
            return redirect(url_for('auth.register'))
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {e}")  # Log per il debugging
            flash("Si è verificato un errore durante la registrazione", "error")
            return redirect(url_for('auth.register'))
        
        flash("Registrazione completata", "success")
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

# Gestisce il login dell'utente
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per hour", methods=["POST"])  # Limita le richieste POST a 5 all'ora (no bruteforce)
@anonymous_required
def login():
    if request.method == 'POST':
        username = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not password:
            flash("Inserisci username e password", "error")
            return redirect(url_for('auth.login'))
        
        try:
            # Cerco lo user corrispondente
            user = User.query.filter_by(username=username).first()
            if not user or not user.is_valid:
                flash("Utente non trovato o non caricato correttamente", "error")
                return redirect(url_for('auth.login'))
            
            # Controllo tra la password dell'utente e l'hash della password inserita
            if not check_password_hash(user.password, password):
                flash("Password errata", "error")
                return redirect(url_for('auth.login'))
                
            login_user(user, True, timedelta(minutes=5))
            # Avvisa che l'identita dell'utente è cambiata(si passa da anonimo a un nuovo user.id)
            identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
    
        except Exception:
            flash("Si è verificato un errore durante la registrazione", "error")
            return redirect(url_for('auth.login'))
        
        flash('Login avvenuto correttamente', 'success')
        return redirect(url_for('profile.select'))
            
    return render_template('login.html')

# Gestisce il logout dell'utente
@app.route('/logout', methods=['GET'])
def logout():
    # Termino la sessione
    logout_user()
    # Remove session keys set by Flask-Principal
    # Dato che la sessione è un dizionario, dopo il login, Flask-Principal crea anche due chiavi: identity.name, identity.auth_type. QUindi finita la sessione, eliminiamo anche i valore associato a queste due chiavi
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Rimuovo tutte le chiavi utilizzate per il filtro dei prodotti e per il carrello
    session.pop('selected_products', None)
    session.pop('selected_categories', None)
    session.pop('min_price',None)
    session.pop('max_price',None)
    session.pop('current_profile_id', None)

    # Dice a Flask_principal che l'utente diventa anonimo
    identity_changed.send(app,identity=AnonymousIdentity())
    flash("Logout avvenuto correttamente", "success")
    return redirect(url_for('auth.home'))