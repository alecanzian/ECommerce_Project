from flask import Blueprint, flash, render_template, session, redirect, request, url_for
from flask_login import login_required, current_user
from extensions.database import Notification, Cart, Order, OrderProduct, Profile, db, Product, Category, get_user_orders#, Order
from extensions.princ import buyer_required, seller_required
from sqlalchemy import desc

app = Blueprint('notifications', __name__)

@app.route('/notifications')
@login_required
def view():
    # Fetch all notifications for the current user
    notifications = Notification.query.filter_by(receiver_id=current_user.id).order_by(desc(Notification.timestamp)).all()
    
    return render_template('notifications.html', notifications=notifications)

@app.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete(notification_id):
    notification = Notification.query.get(notification_id)
    if notification and notification.receiver_id == current_user.id:
        db.session.delete(notification)
        db.session.commit()
        flash('Notifica cancellata', 'success')
    else:
        flash('Errore: Notifica non trovata o non autorizzato', 'danger')
    return redirect(url_for('notifications.view'))

@app.route('/notifications/delete/all', methods=['POST'])
@login_required
def delete_all():
    notifications = Notification.query.filter_by(receiver_id=current_user.id).all()
    for notification in notifications:
        db.session.delete(notification)
    db.session.commit()
    flash('Tutte le notifiche sono state cancellate', 'success')
    return redirect(url_for('notifications.view'))
