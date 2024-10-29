from sqlite3 import IntegrityError
from flask import Blueprint, abort, render_template, redirect, url_for, request, session, flash
from flask_login import login_required, fresh_login_required, current_user
from extensions.database import Profile, State, User, Role, Category, db
from extensions.princ import admin_required
from datetime import date

app = Blueprint('profile', __name__)

# Gestisce la selezione del profilo dopo il login
@app.route('/profile/select', methods = ['GET'])
@login_required
@fresh_login_required
def select():
    return render_template('profile_selection.html')

# Gestisce l'indirizzamento dopo la scelta del profilo
@app.route('/profile/select/<int:profile_id>/<int:action>', methods = ['GET'])
@login_required
@fresh_login_required
def select_id(profile_id, action):
    # Action deve corrispondere a determinati valori
    if action != 0 and  action != 1:
        abort(404)
    try:
        # Cerco se il profilo corrente corrisponde a un profilo associato all'utente
        profile = next((p for p in current_user.profiles if p.id == profile_id),None)
        if not profile or not profile.is_valid:                
            flash('Profilo non trovato o non caricato correttamente', 'error')
            return redirect(url_for('auth.logout'))

        # Setto il profilo corrente che sta operando
        session['current_profile_id'] = profile.id
    except Exception:
        flash("Si è verificato un errore di database. Riprova più tardi", "error")
        return redirect(url_for('auth.logout'))
    
    flash('Profilo aggiornato correttamente', "success")
    if action == 0:
        return redirect(url_for('shop.shop'))
    else:
        return redirect(url_for('shop.shop'))

# Gestisce la creazione di un nuovo profilo
@app.route('/profile/add/<int:action>', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def add(action):
    # Action deve corrispondere a determinati valori
    if action != 0 and action != 1:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        birth_date = request.form.get('birth_date')
        
        # Controllo i dati del form
        if not name or not surname or not birth_date:
            flash('Inserisci tutti i campi', 'error')
            return redirect(url_for('profile.add', action = action))
        
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
                return redirect(url_for('profile.add', action = action))

            # Controlla se la data è troppo indietro (più di 100 anni fa)
            if birth_date < earliest_date:
                flash(f"L'anno di nascita deve essere compreso tra {earliest_date.year} e {current_date.year}.")
                return redirect(url_for('profile.add', action = action))
            
            new_profile = Profile(name=name, surname=surname, birth_date=birth_date, user_id=current_user.id)
            db.session.add(new_profile)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            flash('Profilo già esistente', "error")
            if action == 0:
                return redirect(url_for('profile.select'))
            else:
                return redirect(url_for('account.view'))
        except Exception:
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi.', "error")
            if action == 0:
                return redirect(url_for('profile.select'))
            else:
                return redirect(url_for('account.view'))
            
        flash('Profilo aggiunto correttamente', 'success')
        if action == 0:
            return redirect(url_for('profile.select'))
        else:
            return redirect(url_for('account.view'))
        
    return render_template('add_profile.html', action=action)

# Gestisce la modifica di un profilo dell'utente
@app.route('/profile/modify/<int:profile_id>', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def modify(profile_id):

    try:
        # Cerco se il profilo corrente corrisponde a un profilo associato all'utente
        profile = next((p for p in current_user.profiles if p.id == profile_id),None)
        if not profile or not profile.is_valid:                
            flash('Profilo non trovato o non caricato correttamente', 'error')
            return redirect(url_for('auth.logout'))
        
    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi','error')
        return redirect(url_for('auth.logout'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        image_url = request.form.get('image_url')
        birth_date = request.form.get('birth_date')

        # Controllo dei dati del form
        if not name or not surname or not image_url or not birth_date:
            flash('Inserisci tutti i dati richiesti', 'error')
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

            db.session.commit()

        except Exception:
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi.', "error")
            return redirect(url_for('account.view'))
        
        flash('Profilo aggiornato con successo')
        return redirect(url_for('account.view'))
    
    return render_template('modify_profile.html', profile=profile)

# Gestisce l'eliminazione del profilo e di tutte le sue informazioni
@app.route('/profile/delete/<int:profile_id>', methods=['GET'])
@login_required
@fresh_login_required
def delete(profile_id):
    try:
        # Cerco se il profilo corrente corrisponde a un profilo associato all'utente
        profile = next((p for p in current_user.profiles if p.id == profile_id),None)
        if not profile or not profile.is_valid:                
            flash('Profilo non trovato o non caricato correttamente', 'error')
            return redirect(url_for('auth.logout'))
        
        # Se è presente un solo profilo, allora non posso eliminarlo, altrimenti non avrei un profilo con cui navigare lo shop
        if len(current_user.profiles) <= 1:
            flash("Non puoi eliminare l'unico profilo rimanente.", 'error')
            return redirect(url_for('account.view'))
        
        # Elimino tutti gli item, associati a quel prodotto, dei carrelli degli altri utenti 
        for item in profile.cart_items:
            db.session.delete(item)

        # Elimino il prodilo
        db.session.delete(profile)

        # Se il profilo eliminato corrispondeva al profilo corrente, allora associa il profilo corrente al primo profilo disponibile
        if profile.id == session['current_profile_id']:
            session['current_profile_id'] = current_user.profiles[0].id
        db.session.commit()

    except Exception:
        db.session.rollback()
        flash('Si è verificato un errore di database. Riprova più tardi.', "error")
        return redirect(url_for('account.view'))
    
    flash('Profilo eliminato correttamente', "success")
    return redirect(url_for('account.view')) 

# Gestisce la visualizzazione di tutte le informazioni del database(SOLO PER L'ADMIN)
@app.route('/accounts/info', methods = ['GET'])
@login_required
@fresh_login_required
@admin_required
def info():
    # Ricaviamo tutti gli utenti della tabella User, e tutte le tabelle necessarie affinchè il database funzioni correttamente
    try:
        all_users = User.query.all()
        all_roles = Role.query.all()
        all_categories = Category.query.all()
        all_states = State.query.all()
    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi.', "error")
        return redirect(url_for('account.view'))
    return render_template('info.html', users=all_users, roles=all_roles, categories=all_categories, states = all_states)
