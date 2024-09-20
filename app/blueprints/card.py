from datetime import date
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import current_user, login_required, fresh_login_required
from flask_migrate import current
from extensions.princ import seller_required
from extensions.database import Address, Card, Product, Role, db
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad, unpad

app = Blueprint('card', __name__)

# Funzione per generare una chiave AES (32 byte per AES-256)
def generate_key():
    return os.urandom(32)

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


@app.route('/card/add', methods = ['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        act = (request.form.get('action'))
        try:

            name = request.form.get('name')
            surname = request.form.get('surname')
            card_number = request.form.get('card_number')
            expiration_month = request.form.get('expiration_month')
            expiration_year = request.form.get('expiration_year')
            card_type = request.form.get('card_type')

            if not name or not surname or not card_number or not expiration_month or not expiration_year or not card_type:
                flash('Please fill all fields', 'ERROR')
                return render_template('add_card.html')
            
            if card_type == 'credit' and len(card_number) != 16:
                flash('Repeat again','ERROR')
                return render_template('add_card.html')
            elif card_type == 'debit' and len(card_number) != 19:
                flash('Repeat again','ERROR')
                return render_template('add_card.html')
            

            current_date = date.today()
            if int(expiration_month) < current_date.month or int(expiration_year) < current_date.year:
                flash("La data di scadenza non può essere nel passato.")
                return render_template('add_card.html')

            key = derive_key(current_app.config['SECRET_KEY'])
            # Crittografa i dati
            encrypted_pan = encrypt_data(key, card_number)
            encrypted_expiration_month = encrypt_data(key, expiration_month)
            encrypted_expiration_year = encrypt_data(key, expiration_year)
            
            last_four = card_number[-4:]
            
            new_card = Card(name = name, surname = surname, PAN = encrypted_pan, last_digits=last_four, expiration_month = encrypted_expiration_month, expiration_year = encrypted_expiration_year, card_type = card_type, user_id =current_user.id)
            db.session.add(new_card)
            db.session.commit()

            flash('Card added successfully', 'SUCCESS')
            action = int(act)
            if action == 0:
                return redirect(url_for('account.view'))
            elif action == 1:
                return redirect(url_for('card.add'))
            elif action == 2:
                return redirect(url_for('card.add'))
        
        except Exception as e:
            print(e)
            flash('Si è verificato un errore nel database-1. Riprova più tardi.', 'ERROR')
            action = int(act)
            if action == 0:
                return redirect(url_for('account.view'))
            elif action == 1:
                return redirect(url_for('account.view'))
            elif action == 2:
                return redirect(url_for('account.view'))
    return render_template('add_card.html')

@app.route('/card/delete/<int:card_id>', methods = ['GET'])
@login_required
def delete(card_id):
    try:
        card = next((card for card in current_user.cards if card.id == card_id), None)
        if not card:
            flash('Card not found', 'ERROR')
            return redirect(url_for('account.view'))
        db.session.delete(card)
        db.session.commit()
        flash('Card deleted successfully', 'SUCCESS')
        return redirect(url_for('account.view'))
    except Exception as e:
        print(e)
        flash('Si è verificato un errore nel database-1. Riprova più', 'ERROR')
        return redirect(url_for('account.view'))


        
