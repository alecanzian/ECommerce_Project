from flask import Blueprint, flash, render_template, session, redirect, request, url_for
from flask_login import login_required, current_user
from extensions.database import Cart, Order, OrderProduct, Product, Notification, db
from extensions.princ import buyer_required

app = Blueprint('cart', __name__)

@app.route('/cart', methods = ['GET'])
@login_required
@buyer_required
def cart():
    return render_template('cart.html')

@app.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.filter_by(id = product_id).first()
    for item in current_user.cart_items:
        if item.product_id == product.id:
            flash('Prodotto già nel carrello', 'fail')
            return redirect(url_for('product.access_product', product_id=product_id))
        
    if product.availability == 0:
        flash('Prodotto non disponibile', 'fail')
        return redirect(url_for('product.access_product', product_id=product_id))
    
    item = Cart(profile_id = session['current_profile_id'], user_id = current_user.id, product_id = product.id, quantity=1)
    db.session.add(item)
    db.session.commit()
    
    flash('Prodotto aggiunto correttamente al carrello', "success")
    #return redirect(url_for('product.access_product', product_id=product_id))
    return redirect(url_for('cart.cart'))

@app.route('/delete_item_from_cart/<int:item_id>', methods = ['GET'])
@login_required
def delete_item_from_cart(item_id):
    item = next((item for item in current_user.cart_items if item.id == item_id), None)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Prodotto rimosso correttamente dal carrello', "success")
        return redirect(url_for('cart.cart'))
    
    flash('Prodotto non trovato nel carrello', "error")
    return redirect(url_for('cart.cart'))

@app.route('/order_cart_items', methods = ['GET', 'POST'])
@login_required
def order_cart_items():
    if request.method == 'POST':
        address_id = int(request.form.get('selected_address_id'))
        card_id = int(request.form.get('selected_card_id'))

        if not address_id or not card_id:
            flash('Indirizzo non valido', 'fail')
            return redirect(url_for('cart.order_cart_items'))
        try:
            address = next((address for address in current_user.addresses if address.id == address_id),None)
            if not address:
                flash('Indirizzo non trovato', 'fail')
                return redirect(url_for('cart.order_cart_items'))
            
            card = next((card for card in current_user.cards if card.id == card_id), None)
            if not card:
                flash('Carta non trovata', 'fail')
                return redirect(url_for('cart.order_cart_items'))

            items = current_user.cart_items
            if not items:
                flash('Carrello vuoto', 'fail')
                return redirect(url_for('shop.shop'))
            
            #profile = Profile.query.filter_by(id = session['current_profile_id']).first()
            #if not profile:
            #     flash('Profilo non trovato', 'fail')
            #     return redirect(url_for('cart.cart'))
            address = address.street + ", " + str(address.postal_code) +", " + address.city + ", " + address.province + ", " + address.country
            new_order = Order(user_id = current_user.id, address = address, total_price = 0.0)
            db.session.add(new_order)
            db.session.flush()

            total_price = 0.0
            for item in items:
                total_price += item.product.price * item.quantity
                new_order_product = OrderProduct(order_id = new_order.id, product_id = item.product_id, product_name = item.product.name, quantity = item.quantity)
                db.session.add(new_order_product)
                item.product.availability-=item.quantity
                db.session.delete(item)

                notification = Notification(
                    sender_id=current_user.id,  # The user who changed the state
                    receiver_id=item.product.user_id,  # The user who placed the order
                    type='Nuovo ordine',
                    product_name=item.product.name,
                    order_id=new_order.id
                )
                db.session.add(notification)
                #current_user.seller_information.profit += item.product.price * item.quantity
                
            new_order.total_price = total_price
            db.session.commit()
            
            flash('Ordine avvenuto correttamente',"success")
            return redirect(url_for('shop.orders'))
        except Exception as e:
            print(f"Errore durante l'operazione: {str(e)}")
            db.session.rollback()
            flash('Si è verificato un errore di database4. Riprova più tardi',"error")
            return redirect(url_for('cart.cart'))
        
    if not current_user.cards or not current_user.addresses:
        flash('Devi avere almeno una carta di credito e un indirizzo per poter continuare con l\'acquisto', 'fail')
        return redirect(url_for('cart.cart'))
    return render_template('order_cart_items.html')

@app.route('/change_quantity_cart_item/<int:item_id>', methods = ['POST'])
@login_required
def change_quantity_cart_item(item_id):
    quantity = int(request.form.get('quantity'))
    if not quantity:
        flash('Inserisci la quantità prima di premere Applica', 'fail')
        return redirect(url_for('cart.cart'))
    
    try:
        item = next((i for i in current_user.cart_items if i.id == item_id), None)
        if not item:
            flash('Prodotto non trovato', "error")
            return redirect(url_for('cart.cart'))
        
        item.quantity = quantity
        db.session.commit()
        
        flash('La quantità è stata aggiornata correttamente', "success")
        return redirect(url_for('cart.cart'))
    except Exception as e:
        db.session.rollback()
        print(f"Errore durante l'operazione: {str(e)}")
        flash('Si è verificato un errore di database5. Riprova più tardi',"error")
        return redirect(url_for('cart.cart'))