from flask import Blueprint, abort, render_template, request, flash, redirect, url_for, current_app
from flask_login import current_user, login_required
from extensions.database import Card, db
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad
from datetime import date
import os
from sqlalchemy.exc import IntegrityError

app = Blueprint('card', __name__)

# Funzione per generare una chiave AES (32 byte per AES-256)
def generate_key():
    return os.urandom(32)
# Funzione per codificare una stringa usando la cifratura AES
def encrypt_data(key, data):
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # Applica il padding
    padded_data = pad(data.encode('utf-8'), AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    return iv + encrypted_data  # Salva anche l'iv con i dati crittografati

# Funzione per derivare una chiave dalla SECRET_KEY
def derive_key(secret_key):
    return secret_key[:32].encode('utf-8')  # Usa i primi 32 byte della SECRET_KEY

# Gestisce la creazione di una nuova carta di pagamento
@app.route('/card/add/<string:action>', methods = ['GET', 'POST'])
@login_required
def add(action):

    # Action deve corrispondere con determinati valori
    if not action or (action != 'profile' and  action != 'order_cart_items' and not action.isdigit()):
        abort(404)
    
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        card_number = request.form.get('card_number')
        expiration_month = request.form.get('expiration_month')
        expiration_year = request.form.get('expiration_year')
        card_type = request.form.get('card_type')

        # Controllo i dati del form
        if not name or not surname or not card_number or not expiration_month or not expiration_year or not card_type:
            flash("Inserisci tutti i campi", "error")
            return redirect(url_for('card.add', action = action))
            #return render_template('add_card.html', action = action)
        
        if card_type == 'credit' and len(card_number) != 16:
            flash("Lunghezza numero di carta non valida. Deve essere di 16 cifre", "error")
            return redirect(url_for('card.add', action = action))
        
        if card_type == 'debit' and len(card_number) != 19:
            flash("Lunghezza numero di carta non valida. Deve essere di 19 cifre", "error")
            return redirect(url_for('card.add', action = action))

        try:
            current_date = date.today()
            if int(expiration_year) < current_date.year or (int(expiration_month) < current_date.month and int(expiration_year == current_date.year)):
                flash("La data di scadenza non può essere nel passato", "error")
                return redirect(url_for('card.add', action = action))

            key = derive_key(current_app.config['SECRET_KEY'])
            
            # Crittografa i dati
            encrypted_pan = encrypt_data(key, card_number)
            encrypted_expiration_month = encrypt_data(key, expiration_month)
            encrypted_expiration_year = encrypt_data(key, expiration_year)
            
            last_four = card_number[-4:]
            
            new_card = Card(name = name, surname = surname, pan = encrypted_pan, last_digits=last_four, expiration_month = encrypted_expiration_month, expiration_year = encrypted_expiration_year, card_type = card_type, user_id =current_user.id)
            db.session.add(new_card)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            flash('Carta già esistente', 'error')
            return redirect(url_for('card.add', action = action))
        except Exception:
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi','error')
            if action == 'profile':
                return redirect(url_for('account.view'))
            elif action == 'order_cart_items':
                return redirect(url_for('cart.order_cart_items'))
            else:
                # action è un intero e indica l'id del prodotto
                return redirect(url_for('product.order_product', product_id = int(action)))
        
        flash("Carta aggiunta correttamente", "success")
        if action == 'profile':
            return redirect(url_for('account.view'))
        elif action == 'order_cart_items':
            return redirect(url_for('cart.order_cart_items'))
        else:
            # action è un intero e indica l'id del prodotto
            return redirect(url_for('product.order_product', product_id = int(action)))
            
    return render_template('add_card.html', action = action)

# Gestisce l'eliminazione di una carta dell'utente
@app.route('/card/delete/<int:card_id>', methods = ['GET'])
@login_required
def delete(card_id):

    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    try:
        # Controllo se la carta esiste e se appartiene allo user
        card = next((card for card in current_user.cards if card.id == card_id), None)
        if not card or not card.is_valid:
            flash("Carta non trovata o non caricata correttamente", "error")
            return redirect(url_for('account.view'))
        
        db.session.delete(card)
        db.session.commit()
    except AttributeError:
        db.session.rollback()
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    except Exception:
        db.session.rollback()
        flash("Si è verificato un errore di sistema", "error")
        return redirect(url_for('account.view'))

    flash("Carta eliminata con successo", "success")
    return redirect(url_for('account.view'))