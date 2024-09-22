from sqlite3 import IntegrityError
from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from flask_login import login_required, fresh_login_required, current_user, logout_user
from extensions.database import Address, Cart, Order, OrderProduct, Profile, User, Product, Role, Category, db
from extensions.princ import buyer_required, admin_required, admin_permission, buyer_permission
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date

app = Blueprint('profile', __name__)

@app.route('/profile/select', methods = ['GET'])
@login_required
@fresh_login_required
def select():
    return render_template('profile_selection.html')

@app.route('/profile/select/<int:profile_id>/<int:action>', methods = ['GET'])
@login_required
@fresh_login_required
def select_id(profile_id, action):
    try:
        profile = next((p for p in current_user.profiles if p.id == profile_id),None)
        if not profile:                
            flash('Il profilo selezionato non esiste', "error")
            return redirect(url_for('shop.shop'))

        # Here you can set the selected profile in the session or any other logic
        session['current_profile_id'] = profile.id
        flash('Profilo aggiornato con successo', "success")
        if action == 0:
            return redirect(url_for('shop.shop'))
        elif action == 1:
            return redirect(url_for('shop.shop'))
        elif action == 2:
            return redirect(url_for('cart.cart'))
        else:
            return redirect(url_for('auth.logout'))
    except Exception:
        flash('Si è verificato un errore', "error")
        if action == 0:
            return redirect(url_for('shop.shop'))
        elif action == 1:
            return redirect(url_for('shop.shop'))
        elif action == 2:
            return redirect(url_for('cart.cart'))
        else:
            return redirect(url_for('auth.logout'))

@app.route('/profile/add/<int:action>', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def add(action):  
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        birth_date = date.fromisoformat(request.form.get('birth_date'))

        if not name or not surname or not birth_date:
            flash('Inserisci tutti i campi', 'fail')
            return render_template('add_profile.html', action = action)
        # Begin database session
        #db.session.begin()
        try:
            # Create new profile
            new_profile = Profile(name=name, surname=surname, birth_date=birth_date, user_id=current_user.id)
            db.session.add(new_profile)
            db.session.commit()

            if action == 0:
                return redirect(url_for('profile.select'))
            elif action == 1:
                return redirect(url_for('account.view'))
        except IntegrityError:
            # Handle unique constraint violation (e.g., duplicate profile name)
            db.session.rollback()
            flash('Un porfilo con lo stesso nome esiste già', "error")
            return render_template('add_profile.html', action=action)
        except Exception:
            # Catch other unexpected errors
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi.', "error")
            return redirect(url_for('profile.select'))
        
    return render_template('add_profile.html', action=action)

@app.route('/profile/modify/<int:profile_id>', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def modify(profile_id):

    profile = next((p for p in current_user.profiles if p.id == profile_id), None)

    if not profile:
        flash('Il profilo non è stato trovato', "error")
        return redirect(url_for('account.view'))
        
    if request.method == 'POST':
        # Leggi i dati inviati dal form
        name = request.form.get('name')
        surname = request.form.get('surname')
        image_url = request.form.get('image_url')
        birth_date = (request.form.get('birth_date'))

        if not name or not surname or not image_url or not birth_date:
            flash('Inserisci tutti i dati richiesti', 'warning')
            return redirect(url_for('modify_profile', profile_id=profile_id))
        
        try:
            # Ottieni la data corrente
            current_date = date.today()
            # Definisci l'intervallo massimo per la data di nascita (100 anni fa)
            earliest_date = date(current_date.year - 100, 1, 1)
            # Controllo della data di nascita
            birth_date = date.fromisoformat(birth_date)

            # Controlla se la data è nel futuro
            if birth_date > current_date:
                flash("La data di nascita non può essere nel futuro.")
                return redirect(url_for('profile.modify', profile_id=profile_id))

            # Controlla se la data è troppo indietro (più di 100 anni fa)
            if birth_date < earliest_date:
                flash(f"L'anno di nascita deve essere compreso tra {earliest_date.year} e {current_date.year}.")
                return redirect(url_for('profile.modify', profile_id=profile_id))

            profile.birth_date = birth_date
            profile.name = name
            profile.surname = surname
            profile.image_url = image_url

            for p in profile.orders:
                p.profile_name = name

            db.session.commit()
            
            flash('Profilo aggiornato con successo')
            return redirect(url_for('account.view'))

        except ValueError:
            flash('Formato della data non valido.',"error")
            return redirect(url_for('profile.modify', profile_id=profile_id))
        except Exception as e:
            print(f"Errore durante l'operazione: {str(e)}")
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi.', "error")
            return redirect(url_for('account.view'))
    
    return render_template('modify_profile.html', profile=profile)

@app.route('/profile/delete/<int:profile_id>', methods=['GET'])
@login_required
@fresh_login_required
def delete(profile_id):
    # Begin database session
    #db.session.begin()
    try:
        profile = next((p for p in current_user.profiles if p.id == profile_id), None)
        
        if not profile:
            flash('Il profilo non è stato trovato', "error")
            return redirect(url_for('account.view'))
        
        # Se è presente un solo profilo, allora non posso eliminarlo, altrimenti non avrei un profilo con cui navigare lo shop
        if len(current_user.profiles) > 1:
            db.session.delete(profile)

            for item in profile.cart_items:
                db.session.delete(item)

            db.session.commit()
            if profile.id == session['current_profile_id']:
                session['current_profile_id'] = current_user.profiles[0].id
            flash('Profilo eliminato correttamente', "success")
            return redirect(url_for('account.view')) 
        else:
            flash("Non puoi eliminare l'unico profilo rimanente.", 'fail')
            return redirect(url_for('account.view'))
    except Exception:
        db.session.rollback()
        flash('Si è verificato un errore di database. Riprova più tardi.', "error")
        return redirect(url_for('account.view'))

@app.route('/profile/info', methods = ['GET'])
@login_required
@fresh_login_required
#@admin_required
#@permission_required(buyer_permission)
def info():
    # Ricaviamo tutti gli utenti della tabella User, tutti i prodotti di Products e tutti i Ruoli
    try:
        all_users = User.query.all()
        all_products = Product.query.all()
        all_roles = Role.query.all()
        all_categories = Category.query.all()
        all_addresses = Address.query.all()
        all_cart_items = Cart.query.all()
    except Exception:
        #flash('Si è verificato un errore di database. Riprova più tardi.', "error")
        flash('La pagina info.html non è stata caricata correttamente',"error")
    return render_template('info.html', users=all_users, products=all_products, roles=all_roles, categories=all_categories, addresses = all_addresses, cart_items = all_cart_items) # Passo anche lo username dell'utente loggato(sarà sempre unico)

# Personalizzazione della pagina profilo
#@app.route('/filtered_profile_information/<int:profile_id>', methods=['GET', 'POST'])
#@login_required
#def filtered_profile_information(profile_id):
#    if profile_id >= 1:
#        # Recupera un singolo profilo in base all'ID tra quelli dell'utente autenticato
#        profile = next((p for p in current_user.profiles if p.id == profile_id), None)
#        if profile:
#            session['filtered_by_profile_id'] = profile.id
#            return redirect(url_for('account.view'))
#        else:
#            flash('Profilo non trovato.')
#            return redirect(url_for('account.view'))
#    else:
#        return redirect(url_for('account.view'))