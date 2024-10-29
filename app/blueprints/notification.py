from flask import Blueprint, flash, render_template, redirect, url_for
from flask_login import login_required, current_user
from extensions.database import Notification, db
from sqlalchemy import desc

app = Blueprint('notification', __name__)

# Verifica se l'utente è valido, carica tutte le notifiche del corrente utente in ordine decrescente di timestamp, 
# e le visualizza in una pagina. Se qualcosa va storto, restituisce un messaggio di errore.
@app.route('/notification', methods = ['GET'])
@login_required
def view():
    if not current_user.is_valid:
            flash('L\'utente non è stato caricato correttamente', 'error')
            return redirect(url_for('auth.logout'))
    try:
        notifications = Notification.query.filter_by(receiver_id=current_user.id).order_by(desc(Notification.timestamp)).all()
    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi','error')
        return redirect(url_for('shop.shop'))
    
    return render_template('notifications.html', notifications=notifications)

# Cancella una specifica notifica se esiste, è valida e appartiene all'utente corrente.
# Se non trovata o non valida, restituisce un errore. Cancella dal database la notifica.
@app.route('/notification/delete/<int:notification_id>', methods=['GET'])
@login_required
def delete(notification_id):
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    try:

        notification = db.session.get(Notification, int(notification_id))
        if not notification or not notification.is_valid:
            flash('Notifica non trovata o con caricata correttamente', 'error')
            return redirect(url_for('notification.view'))

        if notification.receiver_id != current_user.id:
            flash('La notifica non appartiene a te', 'error')
            return redirect(url_for('notification.view'))
        
        db.session.delete(notification)
        db.session.commit()

    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi','error')
        return redirect(url_for('shop.shop'))
        
    flash('Notifica cancellata', 'success')
    return redirect(url_for('notification.view'))

# Cancella tutte le notifiche dell'utente corrente. 
# Se qualcosa va storto, restituisce un errore, altrimenti elimina tutte le notifiche trovate nel database.
@app.route('/notification/delete/all', methods=['GET'])
@login_required
def delete_all():
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    try:
        
        notifications = Notification.query.filter_by(receiver_id=current_user.id).all()

        for notification in notifications:
            db.session.delete(notification)
        db.session.commit()

    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi','error')
        return redirect(url_for('shop.shop'))
        
    flash('Tutte le notifiche sono state cancellate', 'success')
    return redirect(url_for('notification.view'))
