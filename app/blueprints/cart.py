from flask import Blueprint, flash, render_template, session, redirect, request, url_for
from flask_login import login_required, current_user
from extensions.database import Cart, Order, OrderProduct, Product, Notification, Profile, db
from extensions.princ import buyer_required
from sqlalchemy.exc import IntegrityError


app = Blueprint('cart', __name__)

# Gestisce la pagina per visualizzare il carrello
@app.route('/cart', methods = ['GET'])
@login_required
@buyer_required
def cart():
    # La chiave deve essere presente, poichè il carrello è legato al profilo e non all'utente
    if 'current_profile_id' not in session:
        flash('Seleziona prima un profilo', 'error')
        return redirect(url_for('profile.select'))
    return render_template('cart.html')

# Gestisce l'aggiunta di un nuovo prodotto al carrello
@app.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
@login_required
def add_to_cart(product_id):

    # La chiave deve essere presente, poichè il carrello è legato al profilo e non all'utente
    if 'current_profile_id' not in session:
        flash('Seleziona prima un profilo', 'error')
        return redirect(url_for('profile.select'))
    
    try:
        # Ricerca del prodotto da aggiungere al carrello
        product = Product.query.filter_by(id = product_id).first()
        if not product or not product.is_valid:
            flash('Prodotto non trovato o non caricato correttamente', 'error')
            return redirect(url_for('shop.shop'))

        # Prodotto presente ma la disponibilità == 0
        if not product.availability:
            flash('Prodotto non disponibile', 'error')
            return redirect(url_for('product.access_product', product_id=product_id))
        
        item = Cart(profile_id = session['current_profile_id'], product_id = product.id, quantity=1)
        db.session.add(item)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Prodotto già presente nel carrello', 'error')
        return redirect(url_for('shop.shop'))
    except Exception:
        db.session.rollback()
        flash('Si è verificato un errore di database. Riprova più tardi','error')
        return redirect(url_for('shop.shop'))
    
    flash('Prodotto aggiunto al carrello correttamente', "success")
    return redirect(url_for('product.access_product', product_id=product_id))

# Gestisce l'eliminazione di un prodotto dal carrello
@app.route('/delete_item_from_cart/<int:item_id>', methods = ['GET'])
@login_required
def delete_item_from_cart(item_id):
    # La chiave deve essere presente, poichè il carrello è legato al profilo e non all'utente
    if 'current_profile_id' not in session:
        flash('Seleziona prima un profilo', 'error')
        return redirect(url_for('profile.select'))
    
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    
    try:
        # Cerco se il profilo corrente corrisponde a un profilo associato all'utente
        profile = next((p for p in current_user.profiles if p.id == session['current_profile_id']), None)
        if not profile or not profile.is_valid:
            flash('Profilo non trovato o non caricato correttamente', 'error')
            return redirect(url_for('auth.logout'))
        
        # Cerco l'item del carrello che contiene il prodotto che si vuole eliminare dal carrello
        item = next((item for item in profile.cart_items if item.id == item_id), None)
        if not item:
            flash('Prodotto non trovato nel carrello', "error")
            return redirect(url_for('cart.cart'))
        
        db.session.delete(item)
        db.session.commit()

    except AttributeError:
        db.session.rollback()
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    except Exception:
        db.session.rollback()
        flash("Si è verificato un errore di sistema", "error")
        return redirect(url_for('cart.cart'))
    
    flash('Prodotto rimosso correttamente dal carrello', "success")
    return redirect(url_for('cart.cart'))

# Gestisce l'ordine di tutti gli item presenti nel carrello
@app.route('/order_cart_items', methods = ['GET', 'POST'])
@login_required
def order_cart_items():
    # La chiave deve essere presente, poichè il carrello è legato al profilo e non all'utente
    if 'current_profile_id' not in session:
        flash('Seleziona prima un profilo', 'error')
        return redirect(url_for('profile.select'))
    
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    
    # L'utente deve avere già un indirizzo e una carta di pagamento
    if not current_user.cards or not current_user.addresses:
        flash('Devi avere almeno una carta di credito e un indirizzo per poter continuare con l\'acquisto', 'error')
        return redirect(url_for('cart.cart'))
    
    if request.method == 'POST':
        address_id = int(request.form.get('selected_address_id'))
        card_id = int(request.form.get('selected_card_id'))
        
        # Controllo i dati del form
        if not address_id or not card_id:
            flash("Inserisci tutti i campi", "error")
            return redirect(url_for('cart.order_cart_items'))
        
        try:
            # Cerco se il profilo corrente corrisponde a un profilo associato all'utente
            profile = next((p for p in current_user.profiles if p.id == session['current_profile_id']), None)
            if not profile or not profile.is_valid:
                flash('Profilo non trovato o non caricato correttamente', 'error')
                return redirect(url_for('profile.select'))
            
            # Lista di item associati al profilo
            cart_items = profile.cart_items
            if not cart_items:
                flash('Carrello vuoto', 'error')
                return redirect(url_for('shop.shop'))
            
            # Cerco l'indirizzo scelto per la spedizione
            address = next((address for address in current_user.addresses if address.id == address_id),None)
            if not address or not address.is_valid:
                flash('Indirizzo non trovato o non caricato correttamente', 'error')
                return redirect(url_for('cart.order_cart_items'))
            
            # Cerco la carta scelta per il pagamento
            card = next((card for card in current_user.cards if card.id == card_id), None)
            if not card or not card.is_valid:
                flash('Carta non trovata o non caricata correttamente', 'error')
                return redirect(url_for('cart.order_cart_items'))

            # creo la stringa address
            address = address.street + ", " + str(address.postal_code) +", " + address.city + ", " + address.province + ", " + address.country
            new_order = Order(user_id = current_user.id, address = address)
            db.session.add(new_order)
            # Necessario perchè  ci serve conoscere order_id
            db.session.flush()

            total_price = 0.0

            for item in cart_items:
                # Aggionro il costo totale dell'ordine
                total_price += item.product.price * item.quantity
                # Creo il nuovo prodotto dell'ordine
                new_order_product = OrderProduct(order_id = new_order.id, product_id = item.product_id, product_name = item.product.name, quantity = item.quantity, seller_id = item.product.user_id)
                db.session.add(new_order_product)
                # Riduco la quantità disponibile del prodotto associato all'item del carrello
                item.product.availability-=item.quantity
                # Elimino l'item dal carrello perchè lo sto per comprare
                db.session.delete(item)

                # Invio la notifica al seller del prodotto
                notification = Notification(
                    sender_id=current_user.id,  # The user who changed the state
                    receiver_id=item.product.user_id,  # The user who placed the order
                    type='Nuovo ordine',
                    product_name=item.product.name,
                    order_id=new_order.id
                )
                db.session.add(notification)

                
                # Aggiorno il profit associato al seller, poichè il seller del prodotto riceverà il pagamento
                item.product.user.seller_information.profit += item.product.price * item.quantity
                
            # Assegno finalmente il costo totale dell'ordine
            new_order.total_price = total_price
            db.session.commit()
        except AttributeError as e:
            print(e)
            db.session.rollback()
            flash('Contenuti dell\'ordine non sono stati caricati correttamente', 'error')
            return redirect(url_for('cart.cart'))

        except Exception as e:
            print(f"Errore durante l'operazione: {str(e)}")
            db.session.rollback()
            flash('Si è verificato un errore di database4. Riprova più tardi',"error")
            return redirect(url_for('cart.cart'))
        
        flash('Ordine avvenuto correttamente',"success")
        return redirect(url_for('shop.orders'))
    
    return render_template('order_cart_items.html')

@app.route('/change_quantity_cart_item/<int:item_id>', methods = ['POST'])
@login_required
def change_quantity_cart_item(item_id):
    if 'current_profile_id' not in session:
        flash('Seleziona prima un profilo', 'error')
        return redirect(url_for('profile.select'))
    
    quantity = request.form.get('quantity')

    # Controllo dei dati del form
    if not quantity:
        flash('Inserisci la quantità', 'error')
        return redirect(url_for('cart.cart'))
    
    try:
        # Cerco se il profilo corrente corrisponde a un profilo associato all'utente
        profile = next((p for p in current_user.profiles if p.id == session['current_profile_id']), None)
        if not profile or not profile.is_valid:
            flash('Profilo non trovato o non caricato correttamente', 'error')
            return redirect(url_for('profile.select'))
        
        # Cerco l'item del carrello che contiene il prodotto che si vuole eliminare dal carrello
        item = next((i for i in profile.cart_items if i.id == item_id), None)
        if not item or not item.is_valid:
            flash('Prodotto non trovato o non caricato correttamente', "error")
            return redirect(url_for('cart.cart'))
        
        # Assegno la quantità scelta
        item.quantity = int(quantity)
        db.session.commit()
        
    except AttributeError:
        db.session.rollback()
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    except Exception:
        db.session.rollback()
        flash('Si è verificato un errore di database5. Riprova più tardi',"error")
        return redirect(url_for('cart.cart'))
    
    flash('La quantità è stata aggiornata correttamente', "success")
    return redirect(url_for('cart.cart'))