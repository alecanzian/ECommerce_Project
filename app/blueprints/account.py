from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import logout_user, current_user, login_required, fresh_login_required
from extensions.database import Role, db
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
            print(f"ciao")
            print(str(password))
            flash('Inserisci la password per confermare la cancellazione dell\'account ')
            return redirect(url_for('profile.profile'))
        
        if current_user.password is None:
            # Gestisci il caso in cui l'utente non ha una password
            flash("Errore: l'utente non ha una password impostata.")
            return redirect(url_for('auth.login'))

        # Se la password è presente, controlla l'hash
        if not check_password_hash(current_user.password, password):
            flash("Password errata.")
            return redirect(url_for('auth.login'))

        # Procedura di eliminazione
        try:
            # Elimina prima tutti i prodotti associati all'utente
            if current_user.has_role('seller'):
                for product in current_user.products:
                    db.session.delete(product)
            # Elimina il profilo dopo aver eliminato i prodotti
            for profile in current_user.profiles:
                db.session.delete(profile) 
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