from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required, fresh_login_required
from extensions.database import Address, Product, Role, db
from werkzeug.security import check_password_hash, generate_password_hash

app = Blueprint('account', __name__)

@app.route('/account', methods = ['GET'])
@login_required
@fresh_login_required
def view():
    return render_template('account.html')

# Route che reindirizza l'utente verso il form per inserire la password e verificare che sia davvero l'utente
@app.route('/account/delete', methods=['GET','POST'])
@login_required
@fresh_login_required
def delete():
    if request.method == 'POST':
        password = request.form.get('password')

        if not password:
            flash('Inserisci la password per confermare la cancellazione dell\'account ')
            return redirect(url_for('account.view'))
        
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

            for order in current_user:
                db.session.delete(order)

            # Elimina l'utente
            db.session.delete(current_user)
            db.session.commit()

            flash('Account eliminato con successo.', 'success')
            return redirect(url_for('auth.logout'))
        
        except AttributeError:
            db.session.rollback()
            flash('L\'utente non ha una password impostata.', 'error')
            return redirect(url_for('account.view'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'eliminazione dell\'account: {str(e)}', 'error')
            return redirect(url_for('account.view'))
        
    return render_template('confirm_password.html', action = 0)

@app.route('/account/change_password', methods=['GET','POST'])
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
            return redirect(url_for('account.view'))
        # Se la nuova password è uguale a quella vecchia
        if(new_password == old_password):
            flash('Password non modificata.', 'error')
            return redirect(url_for('account.view'))
        else:
            current_user.password = generate_password_hash(new_password)
            # Le modifiche vengono salvate nel database
            db.session.commit()

            flash('Password modificata con successo.', 'success')
            return redirect(url_for('account.view'))
    return render_template('change_password.html')

@app.route('/account/become_seller', methods=['GET','POST'])
@login_required
@fresh_login_required
def become_seller():
    if request.method == 'POST':
        password = request.form.get('password')
        # Se la password non corrisponde 
        if current_user.password is None or not check_password_hash(current_user.password, password):
            flash('Password errata. Impossibile eliminare l\'account.', 'error')
            return redirect(url_for('account.view'))
    
        seller_role = Role.query.filter_by(name='seller').first()
        if seller_role:
            # Aggiungi il ruolo "seller" all'utente
            if not current_user.has_role('seller'):
                current_user.roles.append(seller_role)
                db.session.commit()
                flash('Ruolo di seller aggiunto con successo.', 'success')
                return redirect(url_for('account.view'))
            else:
                flash('Ruolo di seller già presente con successo.', 'success')
                return redirect(url_for('account.view'))
        
        else:
            flash(f'Ruolo seller non esistente', 'error')
            return redirect(url_for('account.view'))
    return render_template('confirm_password.html', action = 1)