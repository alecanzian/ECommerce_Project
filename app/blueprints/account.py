from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required, fresh_login_required
from extensions.database import Address, Role, db
from werkzeug.security import check_password_hash, generate_password_hash

app = Blueprint('account', __name__)

# Route che reindirizza l'utente verso il form per inserire la password e verificare che sia davvero l'utente
@app.route('/delete_account', methods=['GET','POST'])
@login_required
@fresh_login_required
def delete_account():
    if request.method == 'POST':
        password = request.form.get('password')

        if not password:
            flash('Inserisci la password per confermare la cancellazione dell\'account ')
            return redirect(url_for('profile.profile'))
        
        if not current_user.password:
                # Gestisci il caso in cui l'utente ha una password = None
                flash('Lutente non ha una password impostata.', 'error')
                return redirect(url_for('auth.login'))

        # Se la password è presente, controlla l'hash
        if not check_password_hash(current_user.password, password):
            flash("Password errata.")
            return redirect(url_for('auth.login'))
        
        db.session.begin()
        try:
            # Elimina prima tutti i prodotti associati all'utente
            if current_user.has_role('seller'):
                for product in current_user.products:
                    for item in product.in_carts:
                        db.session.delete(item)
                    db.session.delete(product)
            # Elimina il profilo dopo aver eliminato i prodotti
            for profile in current_user.profiles:
                db.session.delete(profile) 
            
            # Elimina gli indirizzi dopo aver eliminato i profili
            for address in current_user.addresses:
                db.session.delete(address)

            # Elimina tutti i prodotti sul carrello
            for item in current_user.cart_items:
                db.session.delete(item)

            # Elimina l'utente
            db.session.delete(current_user)
            db.session.commit()

            flash('Account eliminato con successo.', 'success')
            return redirect(url_for('auth.logout'))
        
        except AttributeError:
            db.session.rollback()
            flash('L\'utente non ha una password impostata.', 'error')
            return redirect(url_for('profile.profile'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'eliminazione dell\'account: {str(e)}', 'error')
            return redirect(url_for('profile.profile'))
        
    return render_template('confirm_password.html', action = 0)


@app.route('/change_password', methods=['GET','POST'])
@login_required
@fresh_login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

       # Se la vecchia password non corrisponde con la password corrente
        if current_user.password is None:
            # Gestisci il caso in cui l'utente non ha una password
            flash("Errore: l'utente non ha una password impostata.")
            return redirect(url_for('auth.login'))

        # Se la password è presente, controlla l'hash
        if not check_password_hash(current_user.password, old_password):
            flash("Password errata.")
            return redirect(url_for('auth.login'))

        # Se la nuova password non corrisponde con la sua conferma
        if new_password != confirm_new_password:
            flash('Passwords do not match!', category='error')
            return redirect(url_for('profile.profile'))
        # Se la nuova password è uguale a quella vecchia
        if(new_password == old_password):
            flash('Password non modificata.', 'error')
            return redirect(url_for('profile.profile'))
        else:
            current_user.password = generate_password_hash(new_password)
            # Le modifiche vengono salvate nel database
            db.session.commit()

            flash('Password modificata con successo.', 'success')
            return redirect(url_for('profile.profile'))
    return render_template('change_password.html')

@app.route('/add_seller_role', methods=['GET','POST'])
@login_required
@fresh_login_required
def add_seller_role():
    if request.method == 'POST':
        password = request.form.get('password')
        # Se la password non corrisponde 
        if current_user.password is None or not check_password_hash(current_user.password, password):
            flash('Password errata. Impossibile eliminare l\'account.', 'error')
            return redirect(url_for('profile.profile'))
    
        seller_role = Role.query.filter_by(name='seller').first()
        if seller_role:
            # Aggiungi il ruolo "seller" all'utente
            if not current_user.has_role('seller'):
                current_user.roles.append(seller_role)
                db.session.commit()
                flash('Ruolo di seller aggiunto con successo.', 'success')
                return redirect(url_for('profile.profile'))
            else:
                flash('Ruolo di seller già presente con successo.', 'success')
                return redirect(url_for('profile.profile'))
        
        else:
            flash(f'Ruolo seller non esistente', 'error')
            return redirect(url_for('profile.profile'))
    return render_template('confirm_password.html', action = 1)

@app.route('/add_address', methods = ['GET','POST'])
@login_required
@fresh_login_required
def add_address():
    if request.method == 'POST':
        street = request.form.get('street')
        postal_code = request.form.get('postal_code')
        city = request.form.get('city')
        province = request.form.get('province')
        country = request.form.get('country')

        user_id = current_user.id

        for a in current_user.addresses:
            if a.street.replace(" ", "").lower() == street.replace(" ", "").lower():
                flash('Indirizzo già presente.', 'error')
                return redirect(url_for('account.add_address'))
        address = Address(street = street, postal_code = postal_code, city = city, province = province, country = country, user_id = user_id)
        db.session.add(address)
        current_user.addresses.append(address)
        db.session.commit()
        flash('Indirizzo aggiunto con successo.', 'message')
        return redirect(url_for('profile.profile'))

    return render_template('add_address.html')

@app.route('/modify_address/<int:address_id>', methods = ['GET','POST'])
@login_required
@fresh_login_required
def modify_address(address_id):
    address = next((a for a in current_user.addresses if a.id == address_id), None)
    if request.method == 'POST':
        street = request.form.get('street')
        postal_code = request.form.get('postal_code')
        city = request.form.get('city')
        province = request.form.get('province')
        country = request.form.get('country')

        print(address.street)
        for a in current_user.addresses:
            print(a.street)
            if a.id != address.id and a.street.replace(" ", "").lower() == street.replace(" ", "").lower():
                flash('Indirizzo già presente.', 'error')
                return redirect(url_for('account.modify_address', address_id = address.id))
            
        address.street = street
        address.postal_code = postal_code
        address.city = city
        address.province = province
        address.country = country
        
        db.session.commit()
        flash('Indirizzo modificato con successo.', 'message')
        return redirect(url_for('profile.profile'))

    return render_template('modify_address.html', address = address)

@app.route('/delete_address/<int:address_id>', methods = ['GET'])
@login_required
@fresh_login_required
def delete_address(address_id):
    try:
        address = next((a for a in current_user.addresses if a.id == address_id), None)
        
        if not address:
            flash('Indirizzo non trovato', 'error')
            return redirect(url_for('profile.profile'))
        
        db.session.delete(address)
        db.session.commit()

        flash('Indirizzo eliminato con successo.', 'success')
        return redirect(url_for('profile.profile'))
    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi.', 'error')
        return redirect(url_for('profile.profile'))