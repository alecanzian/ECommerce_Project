from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required, fresh_login_required
from extensions.database import Address, db

app = Blueprint('address', __name__)

@app.route('/add_address/<string:action>', methods = ['GET','POST'])
@login_required
@fresh_login_required
def add_address(action):
    if request.method == 'POST':
        street = request.form.get('street')
        postal_code = request.form.get('postal_code')
        city = request.form.get('city')
        province = request.form.get('province')
        country = request.form.get('country')

        user_id = current_user.id

        for a in current_user.addresses:
            if a.street.replace(" ", "").lower() == street.replace(" ", "").lower():
                flash('Indirizzo già presente.', 'error')
                print("ACTION")
                print(action)
                if action == 'profile':
                    return redirect(url_for('profile.profile'))
                elif action == 'order_cart_items':
                    return redirect(url_for('cart.order_cart_items'))
                else:
                    return redirect(url_for('product.order_product', product_id = int(action)))
        address = Address(street = street, postal_code = postal_code, city = city, province = province, country = country, user_id = user_id)
        db.session.add(address)
        current_user.addresses.append(address)
        db.session.commit()
        flash('Indirizzo aggiunto con successo.', 'success')
        print("ACTION")
        print(action)
        if action == 'profile':
            return redirect(url_for('profile.profile'))
        elif action == 'order_cart_items':
            return redirect(url_for('cart.order_cart_items'))
        else:
            print("ACTION")
            print(action)
            return redirect(url_for('product.order_product', product_id = int(action)))

    return render_template('add_address.html', action = action)

@app.route('/modify_address/<int:address_id>', methods = ['GET','POST'])
@login_required
@fresh_login_required
def modify_address(address_id):
    address = next((a for a in current_user.addresses if a.id == address_id), None)
    if request.method == 'POST':
        street = request.form.get('street')
        postal_code = request.form.get('postal_code')
        city = request.form.get('city')
        province = request.form.get('province')
        country = request.form.get('country')

        print(address.street)
        for a in current_user.addresses:
            print(a.street)
            if a.id != address.id and a.street.replace(" ", "").lower() == street.replace(" ", "").lower():
                flash('Indirizzo già presente.', 'error')
                return redirect(url_for('address.modify_address', address_id = address.id))
            
        address.street = street
        address.postal_code = postal_code
        address.city = city
        address.province = province
        address.country = country
        
        db.session.commit()
        flash('Indirizzo modificato con successo.', 'message')
        return redirect(url_for('profile.profile'))

    return render_template('modify_address.html', address = address)

@app.route('/delete_address/<int:address_id>', methods = ['GET'])
@login_required
@fresh_login_required
def delete_address(address_id):
    try:
        address = next((a for a in current_user.addresses if a.id == address_id), None)
        
        if not address:
            flash('Indirizzo non trovato', 'error')
            return redirect(url_for('profile.profile'))
        
        db.session.delete(address)
        db.session.commit()

        flash('Indirizzo eliminato con successo.', 'success')
        return redirect(url_for('profile.profile'))
    except Exception as e:
        db.session.rollback()
        print(f"Errore durante l'operazione: {str(e)}")
        flash('Si è verificato un errore di database. Riprova più tardi.', 'error')
        return redirect(url_for('profile.profile'))