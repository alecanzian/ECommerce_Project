from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required, fresh_login_required
from extensions.princ import seller_required
from extensions.database import Notification, Order, Role, SellerInformation, State, db
from werkzeug.security import check_password_hash, generate_password_hash

app = Blueprint('account', __name__)

# Indirizzo lo suer alla pagina dell'account se l'utente è caricato correttamente
@app.route('/account', methods = ['GET'])
@login_required
@fresh_login_required
def view():
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    return render_template('account.html')

#Se i dati inseriti sono corretti e se l'utente rispetta determinate condizioni, allora viene eliminato l'utente e tutte le sue informazioni correlate
@app.route('/account/delete', methods=['GET','POST'])
@login_required
@fresh_login_required
def delete():
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    
    if request.method == 'POST':
        password = request.form.get('password')

        if not password:
            flash("Inserisci nuovamente la password per confermare la cancellazione dell'account", 'error')
            return redirect(url_for('account.delete'))

        
        try:
            if not check_password_hash(current_user.password, password):
                flash("Password errata", 'error')
                return redirect(url_for('auth.delete'))
            
            consegnato_state = State.query.filter_by(name='Consegnato').first()

            if not consegnato_state or not consegnato_state.is_valid:
                flash("Stato non trovato o non caricato correttamente", 'error')
                return redirect(url_for('account.view'))
            

            if current_user.has_role('seller'):
                # Se esiste almeno un prodotto dell'utente che non è ancora stato consegnato, si eliminano comunque tutti i prodotti ma non si elimina lo user
                orders = Order.query.all()
                if any(order_product.state_id != consegnato_state.id and order_product.seller_id == current_user.id for order in orders for order_product in order.products):
                    for product in current_user.products:
                        for item in product.in_carts:
                            db.session.delete(item)
                        db.session.delete(product)
                        db.session.commit()
                    flash("Non puoi eliminare l'account se hai ancora dei prodotti da consegnare. Tutti i tuoi prodotti già consegnati sono stati eliminati", "error")
                    return redirect(url_for('account.view')) 
                
                # Tutti i prodotti sono stati consegnati, quindi vengono eliminati tutti
                for product in current_user.products:
                    for item in product.in_carts:
                        db.session.delete(item)
                    db.session.delete(product)  

                # Elimina le informazioni del seller
                #db.session.delete(current_user.seller_information)
                # visto che current_user.seller_information non funziona, per ora uso questo
                for tuple in SellerInformation.query.all():
                    if tuple.user_id == current_user.id:
                        db.session.delete(tuple)

            # Se esiste un prodotto ancora da ricevere, allora non si può eliminare l'utente
            if any(order_product.state_id != consegnato_state.id and order.user_id == current_user.id for order in current_user.orders for order_product in order.products):
                flash("Non puoì eliminare l\'account se hai ancora dei prodotti da ricevere", "error")
                return redirect(url_for('account.view'))
                    
            # Elimina il profilo dopo aver eliminato i prodotti
            for profile in current_user.profiles:
                # Elimina tutti i prodotti sul carrello degli altri utenti
                for item in profile.cart_items:
                    db.session.delete(item)
                db.session.delete(profile) 

            # Elimina gli indirizzi
            for address in current_user.addresses:
                db.session.delete(address)

            # Elimina le carte di pagamento
            for card in current_user.cards:
                db.session.delete(card)

            # Elimina gli ordini fatti dell'utente
            for order in current_user.orders:
                for order_product in order.products:
                    db.session.delete(order_product)
                db.session.delete(order)

            #Elimina tutte le notifications ricevute o inviate dall'utente    
            notifications = Notification.query.filter((Notification.sender_id == current_user.id) | (Notification.receiver_id == current_user.id)).all()
            for notification in notifications:
                db.session.delete(notification)

            # Elimina l'utente
            db.session.delete(current_user)
            db.session.commit()

            flash("Account eliminato correttamente", "success")
            return redirect(url_for('auth.logout'))
        
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi','error')
            return redirect(url_for('account.view'))
        
    return render_template('delete_account.html')

#Verifica se le password corrispondono e aggiorna la password dell'utente
@app.route('/account/change_password', methods=['GET','POST'])
@login_required
@fresh_login_required
def change_password():
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')
        
        # Controllo i dati del form
        if not old_password or not new_password or not confirm_new_password:
            flash('Inserisci tutti i campi', 'error')
            return redirect(url_for('account.change_password'))

        # Se la nuova password non corrisponde con la sua conferma
        if new_password != confirm_new_password:
            flash("La nuova password non corrisponde", "error")
            return redirect(url_for('account.view'))
        
        # Se la nuova password è uguale a quella vecchia
        if new_password == old_password:
            flash("La nuova password è uguale a quella vecchia", "error")
            return redirect(url_for('account.view'))
        try:
            # Controllo tra la password dell'utente e l'hash della nuova password
            if not check_password_hash(current_user.password, old_password):
                flash("Password errata", "error")
                return redirect(url_for('auth.login'))

            current_user.password = generate_password_hash(new_password)
            db.session.commit()

        except Exception:
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi','error')
            return redirect(url_for('account.view'))

        flash("Password modificata correttamente", "success")
        return redirect(url_for('account.view'))
    
    return render_template('change_password.html')

# Gestisce le nuove informazioni del seller
@app.route('/account/become_seller', methods=['GET','POST'])
@login_required
@fresh_login_required
def become_seller():
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    
    if current_user.has_role('seller'):
        flash("Sei già un venditore", "error")
        return redirect(url_for('account.view'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        iban = request.form.get('iban')
        
        try:
            # Controllo dei dati del form
            if not iban or len(iban) != 27:
                flash("IBAN non valido", "error")
                return redirect(url_for('account.become_seller'))
            if not password:
                flash('Inserisci tutti i campi', 'error')
                return redirect(url_for('account.become_seller'))
            
            # Controllo tra la password dell'utente e l'hash della nuova password
            if not check_password_hash(current_user.password, password):
                flash("Password errata", "error")
                return redirect(url_for('account.become_seller'))


            seller_role = Role.query.filter_by(name='seller').first()

            if not seller_role or not seller_role.is_valid:
                flash("Ruolo di seller non trovato o non caricato correttamente", 'error')
                return redirect(url_for('account.view'))

            current_user.roles.append(seller_role)                
            new_seller_information = SellerInformation(user_id = current_user.id, iban = iban)
            db.session.add(new_seller_information)
            db.session.commit()
            #info = SellerInformation.query.all()
            
            #if not info:
            #    print("non esiste")
            #else:
            #    for p in info:
            #        print(p.user_id)
            #        print(p.iban)
            #        print(p.profit)
            
            #print(current_user.seller_information.iban)
        except Exception as e:
            print(e)
            flash('Si è verificato un errore di database. Riprova più tardi','error')
            return redirect(url_for('account.view'))
        
        flash("Sei diventato un venditore!", "success")
        return redirect(url_for('account.view'))
    
    return render_template('become_seller.html')

# Gestisce la modifica dell'iban, verificando che i dati siano corretti
@app.route('/account/iban/modify', methods = ['GET', 'POST'])
@login_required
@fresh_login_required
@seller_required
def modify_iban():
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        iban = request.form.get('iban')

        # Controllo dei dati del form
        if not iban or len(iban) != 27:
            flash("IBAN non valido", "error")
            return redirect(url_for('account.modify_iban'))
        if not password:
            flash('Inserisci tutti i campi', 'error')
            return redirect(url_for('account.modify_iban'))
        try:
            # Controllo tra la password dell'utente e l'hash della nuova password
            if not check_password_hash(current_user.password, password):
                flash("Password errata", "error")
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

            current_user.seller_information.iban = iban
            db.session.commit()
        except Exception:
            flash('Si è verificato un errore di database. Riprova più tardi','error')
            return redirect(url_for('account.view'))
        
        flash("IBAN modificato correttamente", "success")
        return redirect(url_for('account.view'))

    return render_template('modify_iban.html')