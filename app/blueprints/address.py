from flask import Blueprint, abort, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required, fresh_login_required
from extensions.database import Address, db
from sqlalchemy.exc import IntegrityError

app = Blueprint('address', __name__)

# Gestisce la creazione di un nuovo indirizzo
@app.route('/account/address/add/<string:action>', methods = ['GET','POST'])
@login_required
@fresh_login_required
def add(action):
    # Action deve corrispondere con determinati valori
    if not action or (action != 'profile' and  action != 'order_cart_items' and not action.isdigit()):
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
        
        try:
            # Controllo dei dati del form
            if not street or not postal_code or len(postal_code) != 5 or not city or not province or not country:
                flash('Inserisci tutti i campi', 'error')
                return redirect(url_for('address.add', action = action))
            
            new_address = Address(street = street, postal_code = postal_code, city = city, province = province, country = country, user_id = current_user.id)
            db.session.add(new_address)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Indirizzo già esistente', 'error')
            return redirect(url_for('address.add', action = action))
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
        
        flash("Indirizzo aggiunto correttamente", "success")
        if action == 'profile':
            return redirect(url_for('account.view'))
        elif action == 'order_cart_items':
            return redirect(url_for('cart.order_cart_items'))
        else:
            # action è un intero e indica l'id del prodotto
            return redirect(url_for('product.order_product', product_id = int(action)))

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
    
    if not address or not address.is_valid:
        flash('Indirizzo non trovato o non caricato correttamente', 'error')
        return redirect(url_for('account.view'))
    
    if request.method == 'POST':
        street = request.form.get('street')
        postal_code = request.form.get('postal_code')
        city = request.form.get('city')
        province = request.form.get('province')
        country = request.form.get('country')

        try:
            # Controllo i dati del form
            if not street or not postal_code or len(postal_code) != 5 or not city or not province or not country:
                flash('Inserisci tutti i campi', 'error')
                return redirect(url_for('address.modify', address_id = address.id))
                
            address.street = street
            address.postal_code = postal_code
            address.city = city
            address.province = province
            address.country = country
            
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Indirizzo già esistente', 'error')
            return redirect(url_for('address.modify', address_id = address.id))
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
        
    except AttributeError:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    except Exception:
        db.session.rollback()
        flash("Si è verificato un errore di database", "error")
        return redirect(url_for('account.view'))
    
    flash("Indirizzo eliminato con successo", "success")
    return redirect(url_for('account.view'))