from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from flask_login import login_required, fresh_login_required, current_user, logout_user
from extensions.database import Profile, User, Product, Role, Category, db
from extensions.princ import buyer_required, admin_required
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date

app = Blueprint('profile', __name__)

@app.route('/info')
#@login_required
#@admin_required
def info():
    # Ricaviamo tutti gli utenti della tabella User, tutti i prodotti di Products e tutti i Ruoli
    all_users = User.query.all()
    all_products = Product.query.all()
    all_roles = Role.query.all()
    all_categories = Category.query.all()
    return render_template('info.html', users=all_users, products=all_products, roles=all_roles, categories=all_categories) # Passo anche lo username dell'utente loggato(sarà sempre unico)

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
    profiles = current_user.profiles
    return render_template('profile_selection.html', profiles=profiles)

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

@app.route('/add_profile', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def add_profile():  
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
            return redirect(url_for('profile.profile_selection'))
    return render_template('add_profile.html')


@app.route('/delete_profile/<profile_id>', methods=['GET'])
@login_required
def delete_profile(profile_id):
    profile = Profile.query.get(profile_id)
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
        flash("Non puoi eliminare l'unico profilo rimanente.", "error")
        return redirect(url_for('profile.profile'))
    

#-----------------------------------
# Da rifare
@app.route('/change_profile/<profile_id>', methods=['POST'])
@login_required
def change_profile(profile_id):
    profile = Profile.query.get(profile_id)
    return render_template('change_profile.html')

@app.route('/preparing_profile_changes/<profile_id>', methods=['GET'])
@login_required
def preparing_profile_changes():
    # ...
    return redirect(url_for('profile.profile'))