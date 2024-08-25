from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import logout_user, current_user, login_required, fresh_login_required
from extensions.database import db
from werkzeug.security import check_password_hash, generate_password_hash

app = Blueprint('account', __name__)
# Route che reindirizza l'utente verso il form per inserire la password e verificare che sia davvero l'utente
@app.route('/account/confirm_delete', methods=['POST'])
@login_required
@fresh_login_required
def confirm_delete():
    if request.method == 'POST':
        return render_template('confirm_delete.html')

@app.route('/account/delete', methods=['POST'])
@login_required
@fresh_login_required
def delete_account():
        password = request.form.get('password')
        # Se la password non corrisponde 
        if current_user.password is None or not check_password_hash(current_user.password, password):
            flash('Password errata. Impossibile eliminare l\'account.', 'error')
            return redirect(url_for('profile.profile'))
        # Procedura di eliminazione
        try:
            # Elimina prima tutti i prodotti associati ai profili dell'utente
            for profile in current_user.profiles:
                if current_user.has_role('seller'):
                    for product in profile.products:
                        db.session.delete(product)
                db.session.delete(profile)  # Elimina il profilo dopo aver eliminato i prodotti
            # Elimina l'utente
            db.session.delete(current_user)
            db.session.commit()

            flash('Account eliminato con successo.', 'success')
            logout_user()  # Disconnette l'utente
            return redirect(url_for('auth.home'))

        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'eliminazione dell\'account: {str(e)}', 'error')
            return redirect(url_for('profile.profile'))

# Route che reindirizza l'utente verso il form per inserire la nuova password
@app.route('/account/change_password', methods=['POST'])
@login_required
@fresh_login_required
def change_password():
    if request.method == 'POST':
        return render_template('new_password.html')

@app.route('/account/save_password', methods=['POST'])
@login_required
@fresh_login_required
def save_password():
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

       # Se la vecchia password non corrisponde con la password corrente
        if current_user.password is None or not check_password_hash(current_user.password, old_password):
            flash('Password errata. Impossibile cambiare password.', 'error')
            return redirect(url_for('profile.profile'))
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
