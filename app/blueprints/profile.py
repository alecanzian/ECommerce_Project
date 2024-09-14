from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from flask_login import login_required, fresh_login_required, current_user, logout_user
from extensions.database import Address, Cart, Profile, User, Product, Role, Category, db
from extensions.princ import buyer_required, admin_required, admin_permission, buyer_permission
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date

app = Blueprint('profile', __name__)

@app.route('/info')
@login_required
#@admin_required
#@permission_required(buyer_permission)
def info():
    # Ricaviamo tutti gli utenti della tabella User, tutti i prodotti di Products e tutti i Ruoli
    all_users = User.query.all()
    all_products = Product.query.all()
    all_roles = Role.query.all()
    all_categories = Category.query.all()
    all_addresses = Address.query.all()
    all_cart_items = Cart.query.all()
    return render_template('info.html', users=all_users, products=all_products, roles=all_roles, categories=all_categories, addresses = all_addresses, cart_items = all_cart_items) # Passo anche lo username dell'utente loggato(sarà sempre unico)

@app.route('/profile')
@login_required
@fresh_login_required
@buyer_required 
def profile():
    return render_template('profile.html')

@app.route('/profile_selection')
@login_required
@fresh_login_required
def profile_selection():
    return render_template('profile_selection.html')

@app.route('/select_profile/<int:profile_id>')
@login_required
@fresh_login_required
@buyer_required
def select_profile(profile_id):
    profile = Profile.query.get(profile_id)
    if profile and profile.user_id == current_user.id:
        # Here you can set the selected profile in the session or any other logic
        session['current_profile_id'] = profile.id
        return redirect(url_for('shop.shop'))
    return redirect(url_for('profile.profile_selection'))

@app.route('/add_profile/<int:action>', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def add_profile(action):  
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        birth_date = date.fromisoformat(request.form.get('birth_date'))
        if name and surname and birth_date:
            for p in current_user.profiles:
                if p.name == name: #and p.surname == surname and p.birth_date == birth_date:
                    flash('Profile already exists', 'error')
                    return redirect(url_for('profile.profile_selection'))
            new_profile = Profile(name=name, surname=surname, birth_date=birth_date, user_id=current_user.id)
            db.session.add(new_profile)
            db.session.commit()
            if action == 0:
                return redirect(url_for('profile.profile_selection'))
            else:
                return redirect(url_for('profile.profile'))
    return render_template('add_profile.html', action = action)


@app.route('/delete_profile/<profile_id>', methods=['GET'])
@login_required
def delete_profile(profile_id):

    profile = next((p for p in current_user.profiles if p.id == profile_id), None)
        
    # Se è presente un solo profilo, allora non posso eliminarlo, altrimenti non avrei un profilo con cui navigare lo shop
    if len(current_user.profiles) > 1:
        if profile:
            db.session.delete(profile)
            db.session.commit()
            if profile.id == session['current_profile_id']:
                session['current_profile_id'] = current_user.profiles[0].id
            flash('Profilo eliminato correttamente', 'message')
            return redirect(url_for('profile.profile'))
        else:
            flash('il profilo non è stato trovato', 'error')
            return redirect(url_for('profile.profile'))
    else:
        flash("Non puoi eliminare l'unico profilo rimanente.", 'message')
        return redirect(url_for('profile.profile'))


@app.route('/modify_profile/<int:profile_id>', methods=['GET', 'POST'])
@login_required
def modify_profile(profile_id):
    profile = next((p for p in current_user.profiles if p.id == profile_id), None)

    if not profile:
        flash('Profilo non trovato', 'error')
        return redirect(url_for('profile.profile'))
        
    if request.method == 'POST':
        # Leggi i dati inviati dal form
        name = request.form.get('name')
        surname = request.form.get('surname')
        image_url = request.form.get('image_url')
        birth_date = (request.form.get('birth_date'))

        
        if name:
            for p in current_user.profiles:
                if p.id != profile.id and name == p.name:
                    flash('Nome già utilizzato')
                    return redirect(url_for('profile.modify_profile', profile_id=profile.id))
            profile.name = name
            
        if surname:
            profile.surname = surname

        if image_url:
            profile.image_url = image_url

        # Ottieni la data corrente
        current_date = date.today()
        # Definisci l'intervallo massimo per la data di nascita (100 anni fa)
        earliest_date = date(current_date.year - 100, 1, 1)

        # Controllo della data di nascita
        if birth_date:
            try:
                birth_date = date.fromisoformat(birth_date)

                # Controlla se la data è nel futuro
                if birth_date > current_date:
                    flash("La data di nascita non può essere nel futuro.")
                    return redirect(url_for('profile.modify_profile', profile_id=profile_id))

                # Controlla se la data è troppo indietro (più di 100 anni fa)
                if birth_date < earliest_date:
                    flash(f"L'anno di nascita deve essere compreso tra {earliest_date.year} e {current_date.year}.")
                    return redirect(url_for('profile.modify_profile', profile_id=profile_id))

                profile.birth_date = birth_date
            except ValueError:
                flash("Formato data non valido.")
                return redirect(url_for('profile.modify_profile', profile_id=profile_id))
        else:
            flash("data vuota non valida")   
            return redirect(url_for('profile.modify_profile', profile_id=profile_id))     
        db.session.commit()
        flash('Profilo aggiornato con successo')
        return redirect(url_for('profile.profile'))
    
    return render_template('modify_profile.html', profile=profile)




























# Personalizzazione della pagina profilo
#@app.route('/filtered_profile_information/<int:profile_id>', methods=['GET', 'POST'])
#@login_required
#def filtered_profile_information(profile_id):
#    if profile_id >= 1:
#        # Recupera un singolo profilo in base all'ID tra quelli dell'utente autenticato
#        profile = next((p for p in current_user.profiles if p.id == profile_id), None)
#        if profile:
#            session['filtered_by_profile_id'] = profile.id
#            return redirect(url_for('profile.profile'))
#        else:
#            flash('Profilo non trovato.')
#            return redirect(url_for('profile.profile'))
#    else:
#        return redirect(url_for('profile.profile'))

