from flask import Blueprint, flash, render_template, session, redirect, request, url_for
from flask_login import login_required, current_user
from extensions.database import Order, OrderProduct, Profile, db, Product, Category, Notification
from extensions.princ import seller_required

app = Blueprint('product', __name__)

# Gestisce l'accesso alla pagina del prodotto
@app.route('/product/<int:product_id>', methods = ['GET'])
def access_product(product_id):
    try:
        # Cerco il prodotto corrispondente
        product = db.session.get(Product, product_id)
        if not product or not product.is_valid:
            flash('Prodotto non trovato o non caricato correttamente',"error")
            return redirect(url_for('shop.shop'))
    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi',"error")
        return redirect(url_for('auth.logout'))
        
    return render_template('product.html', product=product)

# Gestisce la creazione di un prodotto
@app.route('/add_product', methods=['GET','POST'])
@login_required
@seller_required
def add_product():
    if not current_user.is_valid:
        flash('L\'utente non è stato caricato correttamente', 'error')
        return redirect(url_for('auth.logout'))
    try:
        all_categories = Category.query.all()
        if not all_categories:
            flash('Nessuna categoria trovata', 'error')
            return redirect(url_for('account.view'))
    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi','error')
        return redirect(url_for('auth.logout'))

    
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        image_url = request.form.get('image-url')
        description = request.form.get('description')
        availability = request.form.get('availability')
        category_id = request.form.get('category_id')
        
        try:
            # controllo dei dati del form
            if not name or not price  or float(price) < 0.0 or not description or not availability or int(availability) < 0  or not category_id or not image_url.strip():
                flash('Inserisci tutti i campi',"error")
                return redirect(url_for('product.add_product'))
            
            # cerco la categoria selezionata
            category = Category.query.filter_by(id=category_id).first()
            if not category:
                flash('Categoria non trovata', "error")
                return redirect(url_for('account.view'))
            
            new_product = Product(name=name, price=price, user_id=current_user.id, description = description, availability = availability, category_id = category.id, image_url = image_url)

            db.session.add(new_product)
            db.session.commit()

        except Exception:
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi',"error")
            return redirect(url_for('shop.shop'))
        
        flash('Prodotto aggiunto correttamente', "success")
        return redirect(url_for('account.view'))
    
    return render_template('add_product.html', categories = all_categories)

# Gestisce l'eliminazione di un prodotto del seller
@app.route('/delete_product/<int:product_id>', methods = ['GET'])
@login_required
@seller_required
def delete_product(product_id):
    try:
        # Cerco il prodotto corrispondente tra i prodotti del seller
        product = next((p for p in current_user.products if p.id == product_id), None)
        if not product or not product.is_valid:
            flash('Prodotto non trovato o non caricato correttamente',"error")
            return redirect(url_for('shop.shop'))

        for order_product in product.in_order:
            if order_product.state.name != 'Consegnato':
                # Aggiorno la quantità del prodotto a 0 così che non possono arrivare nuovi ordini per quel prodotto
                order_product.product.availability = 0
                db.session.commit()
                flash('Non puoi eliminare un prodotto che non è stato consegnato','error')
                return redirect(url_for('account.view'))
        
        # Elimino tutte le tuple del carrello che si riferiscono a quell'oggetto
        for item in product.in_carts:
            db.session.delete(item)
        
        db.session.delete(product)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Si è verificato un errore di database. Riprova più tardi',"error")
        return redirect(url_for('shop.shop'))
    
    flash('Prodotto eliminato correttamente', "success")
    return redirect(url_for('account.view'))

# gestisce la modifica di un podotto del seller
@app.route('/modify_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
@seller_required
def modify_product(product_id):
    try:
        # Cerco il prodotto corrispondente tra i prodotti del seller
        product = next((p for p in current_user.products if p.id == product_id), None)
        if not product or not product.is_valid:
            flash('Prodotto non trovato o non caricato correttamente',"error")
            return redirect(url_for('shop.shop'))
    except Exception:
            flash('Si è verificato un errore di database. Riprova più tardi',"error")
            return redirect(url_for('shop.shop'))

    if request.method == 'POST':
        # Leggi i dati inviati dal form
        try:
            price = request.form.get('price')
            image_url = request.form.get('image_url')
            description = request.form.get('description')
            availability = request.form.get('availability')

            # Controllo dei dati del form
            if not price or float(price) < 0.0 or not description or not image_url or not availability or int(availability) < 0 or not price or not availability:
                flash('Inserisci tutte le informazioni', 'error')
                return redirect(url_for('product.modify_product'), product_id = product.id)
            
            product.price = float(price)
            product.description = description
            product.image_url = image_url
            product.availability = int(availability)
            
            # Il prodotto non è più disponibile all'ordine, quindi viene rimosso da tutti i carrelli degli utenti
            if product.availability == 0:
                for item in product.in_carts:
                    db.session.delete(item)
            
            db.session.commit()
        
        except Exception:
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi',"error")
            return redirect(url_for('shop.shop'))
        
        flash('Prodotto aggiornato con successo', 'success')
        return redirect(url_for('account.view'))
    
    return render_template('modify_product.html', product=product, categories = Category.query.all())

# Gestisce l'ordine di un unico prodotto, acquistato attraverso il tasto 'acquista'
@app.route('/order_product/<int:product_id>',methods = ['GET', 'POST'])
@login_required
def order_product(product_id):
    if request.method == 'POST':
        
        try:
            quantity = int(request.form.get('quantity'))
            address_id = int(request.form.get('selected_address_id'))
            card_id = int(request.form.get('selected_card_id'))

            # Controllo i dati del form
            if not quantity or not address_id or not card_id:
                flash("Inserisci tutti i campi", "error")
                return redirect(url_for('product.order_product', product_id=product_id))
            
            # Cerco il prodotto da ordinare
            product = Product.query.filter_by(id=product_id).first()
            if not product or not product.is_valid:
                flash('Prodotto non trovato o non caricato correttamente', 'error')
                return redirect(url_for('product.access_product', product_id=product_id))
            
            #Controllo che la quantità sia corretta
            if quantity < 1 or quantity > product.availability:
                flash('Quantità non valida', 'error')
                return redirect(url_for('product.order_product', product_id=product_id))

            # Cerco l'indirizzo scelto per la spediazione
            address = next((a for a in current_user.addresses if a.id == address_id), None)
            if not address or not address.is_valid:
                flash('Indirizzo non valido o non caricato correttamente', 'error')
                return redirect(url_for('product.access_product', product_id=product_id))
            
            # Cerco la carta scelta per il pagamento
            card = next((card for card in current_user.cards if card.id == card_id), None)
            if not card or not card.is_valid:
                flash('Carta non trovata o non caricata correttamente', 'error')
                return redirect(url_for('product.access_product', product_id=product_id))

            ## Creazione della stringa address
            address_name = address.street + ", " + str(address.postal_code) +", " + address.city + ", " + address.province + ", " + address.country

            # Creazione dell'ordine
            new_order = Order(user_id = current_user.id, card_last_digits = card.last_digits, address = address_name, total_price = (product.price * quantity))
            db.session.add(new_order)
            # # Forza la generazione dell'ID per avere new_order.id
            db.session.flush()

            # Aggiungi il prodotto all'ordine
            new_order_product = OrderProduct(order_id=new_order.id, product_id=product.id, product_name = product.name, quantity=quantity, seller_id = product.user_id)
            
            db.session.add(new_order_product)
            # # Forza la generazione dell'ID per avere new_order_product.id
            db.session.flush()
            # Diminuisci la quantità disponibile del prodotto acquistato
            product.availability-=quantity
            
            # Invia una notifica al seller del prodotto
            notification = Notification(
                sender_id=current_user.id,  # The user who changed the state
                receiver_id=product.user_id,  # The user who placed the order
                type='Nuovo ordine',
                order_product_id=new_order_product.id
            )

            db.session.add(notification)

            # Aggiorna il profit del seller
            product.user.seller_information.profit += product.price * quantity

            db.session.commit()
            
        except Exception:
            # In caso di errore, rollback e gestione dell'eccezione
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi.', "error")
            return redirect(url_for('product.access_product', product_id=product_id))
        
        flash('Ordine effettuato correttamente', "success")
        return redirect(url_for('shop.orders'))
    
    elif request.method == 'GET':
        try:
            # Cerco il prodotto da ordinare
            product = Product.query.filter_by(id=product_id).first()
            if not product or not product.is_valid:
                flash('Prodotto non trovato o non caricato correttamente', 'error')
                return redirect(url_for('product.access_product', product_id=product_id))
            
            # Controllo che il prodotto da acquistare non appartenga all'utente stesso
            if current_user.has_role('seller'):
                if product.user_id == current_user.id:
                    flash('Non puoi comprare il prodotto venduto da te', 'error')
                    return redirect(url_for('product.access_product', product_id=product_id))

            # Verifica disponibilità prodotto
            if product.availability == 0:
                flash('Prodotto non disponibile', 'error')
                return redirect(url_for('product.access_product', product_id=product_id))
            
            # Cerco il profilo corrrente
            profile = Profile.query.filter_by(id = session['current_profile_id']).first()
            if not profile or not profile.is_valid:
                flash('Profilo non trovato o non caricato correttamente', 'error')
                return redirect(url_for('product.access_product', product_id=product_id))
            
            # Controllo se il prodotto non sia già all'interno del carrello
            for item in profile.cart_items:
                if item.product_id == product.id:
                    flash('Prodotto già presente nel carrello', 'error')
                    return redirect(url_for('cart.cart'))
            # Se l'utente non possiede almeno una carta e un indirizzo, allora non può procedere all'ordine
            if not current_user.cards or not current_user.addresses:
                flash('Devi avere almeno una carta di credito e un indirizzo per poter continuare con l\'acquisto', 'error')
                return redirect(url_for('product.access_product', product_id=product_id))
        
        except Exception:
            flash('Si è verificato un errore di database. Riprova più tardi',"error")
            return redirect(url_for('product.access_product', product_id=product_id))
        
        return render_template('order_product.html', product = product)