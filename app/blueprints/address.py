from sqlite3 import IntegrityError
from flask import Blueprint, abort, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required, fresh_login_required
from extensions.database import Address, db

app = Blueprint('address', __name__)

# Gestisce la creazione di un nuovo indirizzo
@app.route('/account/address/add/<string:action>', methods = ['GET','POST'])
@login_required
@fresh_login_required
def add(action):
    if not action:
        flash('Azione non riconosciuta', 'error')
        abort(404)
    
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    
    if request.method == 'POST':
        street = request.form.get('street')
        postal_code = request.form.get('postal_code')
        city = request.form.get('city')
        province = request.form.get('province')
        country = request.form.get('country')

        # Controllo dei dati del form
        if not street or not postal_code or not city or not province or not country:
            flash('Inserisci tutti i campi', 'error')
            return redirect(url_for('address.add', action = action))
        
        try:
            # Controllo se esiste già un indirizzo con la stessa via, allora blocca l'azione
            if any(address.street.replace(" ", "").lower() == street.replace(" ", "").lower() for address in current_user.addresses):
                flash("Indirizzo già presente", "error")
                return redirect(url_for('address.add', action = action))
            
            new_address = Address(street = street, postal_code = postal_code, city = city, province = province, country = country, user_id = current_user.id)
            db.session.add(new_address)
            db.session.commit()
        except AttributeError:
            db.session.rollback()
            flash('L\'utente non è stato caricato correttamente', 'error')
            return redirect(url_for('auth.logout'))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi','error')
            return redirect(url_for('shop.shop'))
        
        flash("Indirizzo aggiunto correttamente", "success")
        if action == 'profile':
            return redirect(url_for('account.view'))
        elif action == 'order_cart_items':
            return redirect(url_for('cart.order_cart_items'))
        elif action.isdigit():
            return redirect(url_for('product.order_product', product_id = int(action)))
        else:
            flash('Azione non riconosciuta', 'error')
            return redirect(url_for('shop.shop'))


    return render_template('add_address.html', action = action)

# Gestisce la modifica dell'indirizzo dell'utente
@app.route('/account/address/modify/<int:address_id>', methods = ['GET','POST'])
@login_required
@fresh_login_required
def modify(address_id):

    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    try:
        # Controllo se l'id dell'indirizzo è effettivamente un indirizzo dell'utente, altrimenti restituisce None
        address = next((a for a in current_user.addresses if a.id == address_id), None)
    except AttributeError:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    
    if not address:
        flash('Indirizzo non trovato', 'error')
        return redirect(url_for('account.view'))
    
    if request.method == 'POST':
        street = request.form.get('street')
        postal_code = request.form.get('postal_code')
        city = request.form.get('city')
        province = request.form.get('province')
        country = request.form.get('country')

        # Controllo i dati del form
        if not street or not postal_code or not city or not province or not country:
            flash('Inserisci tutti i campi', 'error')
            return redirect(url_for('address.modify', address_id = address.id))
        try:
            # Controlla se la modifica della via che si vuole apportare coincide con il nome di una via di un altro indirizzo dell'utente
            if any(a.id != address.id and a.street.replace(" ", "").lower() == street.replace(" ", "").lower() for a in current_user.addresses):
                flash("Indirizzo già presente", "error")
                return redirect(url_for('address.modify', address_id = address.id))
                
            address.street = street
            address.postal_code = postal_code
            address.city = city
            address.province = province
            address.country = country
            
            db.session.commit()

        except Exception:
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi','error')
            return redirect(url_for('account.view'))
        
        flash("Indirizzo modificato con successo", "success")
        return redirect(url_for('account.view'))

    return render_template('modify_address.html', address = address)

# Gestisce l'eliminazione dell'utente
@app.route('/account/address/delete/<int:address_id>', methods = ['GET'])
@login_required
@fresh_login_required
def delete(address_id):
    try:
        # Controllo se l'id dell'indirizzo è effettivamente un indirizzo dell'utente, altrimenti restituisce None
        address = next((a for a in current_user.addresses if a.id == address_id), None)
        
        if not address:
            flash("Indirizzo non trovato", "error")
            return redirect(url_for('account.view'))
        
        db.session.delete(address)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Si è verificato un errore di database", "error")
        return redirect(url_for('account.view'))
    
    flash("Indirizzo eliminato con successo", "success")
    return redirect(url_for('account.view'))