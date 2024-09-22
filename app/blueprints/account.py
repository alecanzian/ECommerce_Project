from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required, fresh_login_required
<<<<<<< Updated upstream
from extensions.database import Address, Product, Role, db
=======
from extensions.princ import seller_required
from extensions.database import Role, SellerInformation, State, db
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
            flash('Inserisci la password per confermare la cancellazione dell\'account ')
            return redirect(url_for('profile.profile'))
=======
            flash("Inserisci la password per confermare la cancellazione dell'account", "error")
            return redirect(url_for('account.view'))
>>>>>>> Stashed changes
        
        if not current_user.password:
            # Gestisci il caso in cui l'utente ha una password = None
            flash("L'utente non ha una password impostata", "error")
            return redirect(url_for('auth.login'))

        # Se la password è presente, controlla l'hash
        if not check_password_hash(current_user.password, password):
            flash("Password errata", "error")
            return redirect(url_for('auth.login'))
        
        db.session.begin()
        try:
<<<<<<< Updated upstream
=======
            consegnato_state = State.query.filter_by(name='Consegnato').first()
            if not consegnato_state:
                flash("Stato non trovato", "error")
                return redirect(url_for('account.view'))
                
            if current_user.has_role('seller'):
                for product in current_user.products:
                    if product.in_order.state_id != consegnato_state.id:
                        for product in current_user.products:
                            for item in product.in_carts:
                                db.session.delete(item)
                            db.session.delete(product)                        
                        flash("Non puoi eliminare l'account se hai ancora dei prodotti da consegnare. Tutti i tuoi prodotti sono stati eliminati", "error")
                        return redirect(url_for('account.view'))
                    
            for order in current_user.orders:
                for order_product in order.products:
                    if order_product.state_id != consegnato_state.id:
                        flash("Non puoì eliminare l\'account se hai ancora dei prodotti da ricevere", "error")
                        return redirect(url_for('account.view'))
                    
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
=======
            for order in current_user.orders:
                db.session.delete(order)
            
            #db.session.delete(current_user.seller_information)
            # visto che current_user.seller_information non funziona, per ora uso questo
            for tuple in SellerInformation.query.all():
                if tuple.user_id == current_user.id:
                    db.session.delete(tuple)

>>>>>>> Stashed changes
            # Elimina l'utente
            db.session.delete(current_user)
            db.session.commit()

            flash("Account eliminato con successo", "success")
            return redirect(url_for('auth.logout'))
        
        except AttributeError:
            db.session.rollback()
<<<<<<< Updated upstream
            flash('L\'utente non ha una password impostata.', 'error')
            return redirect(url_for('profile.profile'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'eliminazione dell\'account: {str(e)}', 'error')
            return redirect(url_for('profile.profile'))
=======
            flash("L'utente non ha una password impostata", "error")
            return redirect(url_for('account.view'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Errore durante l'eliminazione dell'account: {str(e)}", "error")
            return redirect(url_for('account.view'))
>>>>>>> Stashed changes
        
    return render_template('confirm_password.html', action = 0)

@app.route('/change_password', methods=['GET','POST'])
@login_required
@fresh_login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

<<<<<<< Updated upstream
       # Se la vecchia password non corrisponde con la password corrente
=======
        # Se la vecchia password non corrisponde con la password corrente
        
        # Gestisci il caso in cui l'utente non ha una password
>>>>>>> Stashed changes
        if current_user.password is None:
            flash("L'utente non ha una password impostata", "error")
            return redirect(url_for('auth.login'))

        # Se la password è presente, controlla l'hash
        if not check_password_hash(current_user.password, old_password):
            flash("Password errata", "error")
            return redirect(url_for('auth.login'))

        # Se la nuova password non corrisponde con la sua conferma
        if new_password != confirm_new_password:
<<<<<<< Updated upstream
            flash('Passwords do not match!', category='error')
            return redirect(url_for('profile.profile'))
        # Se la nuova password è uguale a quella vecchia
        if(new_password == old_password):
            flash('Password non modificata.', 'error')
            return redirect(url_for('profile.profile'))
=======
            flash("La nuova password non corrisponde", "error")
            return redirect(url_for('account.view'))
        
        # Se la nuova password è uguale a quella vecchia
        if new_password == old_password:
            flash("La nuova password è uguale a quella vecchia", "error")
            return redirect(url_for('account.view'))
>>>>>>> Stashed changes
        else:
            current_user.password = generate_password_hash(new_password)
            # Le modifiche vengono salvate nel database
            db.session.commit()

<<<<<<< Updated upstream
            flash('Password modificata con successo.', 'success')
            return redirect(url_for('profile.profile'))
=======
            flash("Password modificata con successo", "success")
            return redirect(url_for('account.view'))
>>>>>>> Stashed changes
    return render_template('change_password.html')

@app.route('/add_seller_role', methods=['GET','POST'])
@login_required
@fresh_login_required
def add_seller_role():
    if request.method == 'POST':
        password = request.form.get('password')
<<<<<<< Updated upstream
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
=======
        iban = request.form.get('iban')
        
        try:
            # Se la password non corrisponde
            if not current_user.password or not check_password_hash(current_user.password, password):
                flash("Password errata", "error")
                return redirect(url_for('account.view'))

            if not iban or len(iban) != 27:
                flash("IBAN non valido", "error")
                return redirect(url_for('account.view'))

            seller_role = Role.query.filter_by(name='seller').first()
            if seller_role:
                current_user.roles.append(seller_role)                
                new_seller_information = SellerInformation(user_id = current_user.id, iban = iban)
                db.session.add(new_seller_information)
                db.session.commit()
                info = SellerInformation.query.filter_by(user_id = current_user.id).first()
                
                if not info:
                    print("non esiste")
                else:
                    print(info.iban)
                
                #print(current_user.seller_information.iban)
                flash("Sei diventato un venditore con successo", "success")
                return redirect(url_for('account.view'))
            else:
                flash(f"Il ruolo venditore non esiste", "error")
                return redirect(url_for('account.view'))
        except Exception as e:
            print(e)
            flash("Errore durante la modifica del ruolo", "error")
            return redirect(url_for('account.view'))

    if current_user.has_role('seller'):
        flash("Sei già un venditore", "error")
        return redirect(url_for('account.view'))
    
    return render_template('become_seller.html')

@app.route('/account/iban/modify', methods = ['GET', 'POST'])
@login_required
@fresh_login_required
@seller_required
def modify_iban():
    if request.method == 'POST':
        password = request.form.get('password')
        iban = request.form.get('iban')
        
        if not password or not current_user.password or not check_password_hash(current_user.password, password):
            flash("Password errata", "error")
            return redirect(url_for('account.modify_iban'))
        
        if not iban or len(iban) != 27:
            flash("IBAN non valido", "error")
            return redirect(url_for('account.modify_iban'))
        
        #stampa di debug
        #info = SellerInformation.query.all()
        #if not info:
        #    print("non esiste")
        #else:
        #    for p in info:
        #        if p.user_id == current_user.id:
        #            print(p.iban)
        #            p.iban = iban

        #current_user.seller_information.iban = iban
        db.session.commit()
        flash("IBAN modificato con successo", "success")
        return redirect(url_for('account.view'))

    return render_template('modify_iban.html')
>>>>>>> Stashed changes
