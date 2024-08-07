from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, fresh_login_required, current_user
from extensions.database import Profile, User, Product, Role, Category, db
from extensions.princ import buyer_required, admin_required
from datetime import date

app = Blueprint('profile', __name__)

@app.route('/info')
@login_required
@admin_required
def info():
    # Ricaviamo tutti gli utenti della tabella User, tutti i prodotti di Products e tutti i Ruoli
    all_users = User.query.all()
    all_products = Product.query.all()
    all_roles = Role.query.all()
    all_categories = Category.query.all()
    return render_template('info.html', users=all_users, products=all_products, roles=all_roles, categories=all_categories, session_user=current_user) # Passo anche lo username dell'utente loggato(sarà sempre unico)

@app.route('/profile')
@login_required
@fresh_login_required
#@buyer_required
def profile():    
    return render_template('profile.html')

@app.route('/profile_selection')
@login_required
@fresh_login_required
#@buyer_required
def profile_selection():
    profiles = current_user.profiles
    return render_template('profile_selection.html', profiles=profiles)

@app.route('/select_profile/<int:profile_id>')
@login_required
def select_profile(profile_id):
    profile = Profile.query.get(profile_id)
    if profile and profile.user_id == current_user.id:
        # Here you can set the selected profile in the session or any other logic
        return redirect(url_for('shop.shop'))
    return redirect(url_for('profile.profile_selection'))

@app.route('/add_profile', methods=['GET', 'POST'])
@login_required
def add_profile():  
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        birth_date = request.form.get('birth_date')
        birth_date = date.fromisoformat(request.form.get('birth_date'))
        if name and surname and birth_date:
            new_profile = Profile(name=name, surname=surname, birth_date=birth_date, user_id=current_user.id)
            db.session.add(new_profile)
            db.session.commit()
            return redirect(url_for('profile.profile_selection'))
    return render_template('add_profile.html')

@app.route('/save_profile', methods=['POST'])
@login_required
@fresh_login_required
@buyer_required
def save_profile():
    username = request.form.get('username')
    
    # Verifica che il nuovo username non sia vuoto
    if username:
        # Esegui ulteriori controlli, come assicurarsi che l'username non sia già preso
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Username already taken.', 'error')
        else:
            current_user.username = username
            db.session.commit()
            flash('Profile updated successfully!', 'success')
    else:
        flash('Username cannot be empty.', 'error')
    
    return redirect(url_for('profile.profile'))