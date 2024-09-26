from flask import Blueprint, flash, render_template, session, redirect, request, url_for
from flask_login import login_required, current_user
from extensions.database import Cart, Order, OrderProduct, Profile, db, Product, Category, Notification, get_user_orders#, Order
from extensions.princ import buyer_required, seller_required

app = Blueprint('product', __name__)

@app.route('/product/<int:product_id>', methods = ['GET'])
@login_required
@buyer_required
def access_product(product_id):
    try:
        product = db.session.get(Product,product_id)
        if not product:
            flash('Il prodotto non esiste',"error")
            return redirect(url_for('shop.shop'))
    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi',"error")
        return redirect(url_for('shop.shop'))
        
    return render_template('product.html', product=product)


@app.route('/add_product', methods=['GET','POST'])
@login_required
@seller_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        image_url = request.form.get('image-url')
        description = request.form.get('description')
        availability = request.form.get('availability')
        category_id = request.form.get('category_id')
        
        try:
            
            category = Category.query.filter_by(id=category_id).first()
            if not category:
                flash('Categoria non trovata', "error")
                return redirect(url_for('account.view'))
            
            #category = Category.query.filter_by(name='Altro').first()

            user_id = current_user.id

            if not image_url:
                new_product = Product(name=name, price=price, user_id=user_id, description = description, availability = availability, category_id = category.id)
            else:
                new_product = Product(name=name, price=price, user_id=user_id, description = description, availability = availability, category_id = category.id, image_url = image_url)

            db.session.add(new_product)
            db.session.commit()

        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi',"error")
            return redirect(url_for('shop.shop'))
        
        flash('Prodotto aggiunto correttamente', "success")
        return redirect(url_for('account.view'))
    
    return render_template('add_product.html', categories = Category.query.all())


@app.route('/delete_product/<int:product_id>', methods = ['GET'])
@login_required
@seller_required
def delete_product(product_id):
    try:
        product = next((p for p in current_user.products if p.id == product_id), None)
        if not product:
            flash('il prodotto non è stato trovato', "error")
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
    
@app.route('/modify_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def modify_product(product_id):
    try:
        product = next((p for p in current_user.products if p.id == product_id), None)
        if not product:
            flash('il prodotto non è stato trovato', "error")
            return redirect(url_for('account.view'))
    except Exception:
            flash('Si è verificato un errore di database. Riprova più tardi',"error")
            return redirect(url_for('shop.shop'))

    if request.method == 'POST':
        # Leggi i dati inviati dal form
        try:
            name = request.form.get('name')
            price = float(request.form.get('price'))
            image_url = request.form.get('image_url')
            description = request.form.get('description')
            availability = int(request.form.get('availability'))
            category_id = request.form.get('category_id')

            if not name or not price or not description or not image_url or not availability or not category_id:
                flash('Inserisci tutte le informazioni', 'FAIL')
                return redirect(url_for('product.modify_product'), product_id = product.id)

            category = Category.query.filter_by(id = category_id).first()
            if not category:
                flash('Categoria non trovata', "error")
                return redirect(url_for('account.view'))
            
            product.name = name
            product.price = price
            product.description = description
            product.image_url = image_url
            product.availability = availability
            product.category_id = category.id
            if availability == 0:
                for item in product.in_carts:
                    db.session.delete(item)
            
            db.session.commit()
        
        except Exception:
            db.session.rollback()
            flash('Si è verificato un errore di database. Riprova più tardi',"error")
            return redirect(url_for('shop.shop'))
        
        flash('Prodotto aggiornato con successo')
        return redirect(url_for('account.view'))
    
    return render_template('modify_product.html', product=product, categories = Category.query.all())

@app.route('/order_product/<int:product_id>',methods = ['GET', 'POST'])
@login_required
def order_product(product_id):
    if request.method == 'POST':
        quantity = int(request.form.get('quantity'))
        address_id = int(request.form.get('selected_address_id'))
        card_id = int(request.form.get('selected_card_id'))
        # Verifica preliminare della quantità e indirizzo
        if not quantity or not address_id or not card_id:
            flash('Inserisci la quantità e l\'indirizzo', 'fail')
            return redirect(url_for('product.order_product', product_id=product_id))
        
        try:
            # Query per il prodotto
            product = Product.query.filter_by(id=product_id).first()
            if not product:
                flash('Prodotto non trovato', 'fail')
                return redirect(url_for('product.access_product', product_id=product_id))
            
            # Query per l'indirizzo
            address = next((a for a in current_user.addresses if a.id == address_id), None)
            if not address:
                flash('Indirizzo non valido', 'fail')
                return redirect(url_for('product.access_product', product_id=product_id))
            
            card = next((card for card in current_user.cards if card.id == card_id), None)
            if not card:
                flash('Carta non trovata', 'fail')
                return redirect(url_for('product.access_product', product_id=product_id))
        except Exception:
            flash('Si è verificato un errore di database1. Riprova più tardi.', "error")
            return redirect(url_for('product.access_product', product_id=product_id))


        # Operazioni critiche sul database in blocco try-except
        try:
            #profile = Profile.query.filter_by(id = session['current_profile_id']).first()
            #if not profile:
            #    flash('Profilo non trovato', 'fail')
            #    return redirect(url_for('product.access_product', product_id=product_id))
            ## Creazione del nuovo ordine
            address_name = address.street + ", " + str(address.postal_code) +", " + address.city + ", " + address.province + ", " + address.country
            new_order = Order(user_id = current_user.id, address = address_name, total_price = (product.price * quantity))
            db.session.add(new_order)
            db.session.flush()  # Forza la generazione dell'ID per l'ordine

            # Aggiungi il prodotto all'ordine
            new_order_product = OrderProduct(order_id=new_order.id, product_id=product.id, product_name = product.name, quantity=quantity, seller_id = product.user_id)
            
            db.session.add(new_order_product)
            product.availability-=quantity
            
            notification = Notification(
                sender_id=current_user.id,  # The user who changed the state
                receiver_id=product.user_id,  # The user who placed the order
                type='Nuovo ordine',
                product_name=product.name,
                order_id=new_order.id
            )

            db.session.add(notification)

            current_user.seller_information.profit += product.price * quantity
            db.session.commit()
            flash('Ordine effettuato con successo', "success")
            return redirect(url_for('shop.orders'))
        except Exception as e:
            # In caso di errore, rollback e gestione dell'eccezione
            db.session.rollback()
            print(f"Errore durante l'operazione: {str(e)}")
            flash('Si è verificato un errore di database2. Riprova più tardi.', "error")
            return redirect(url_for('product.access_product', product_id=product_id))
        
    elif request.method == 'GET':
        try:
            product = Product.query.filter_by(id=product_id).first()
            if not product:
                flash('Prodotto non trovato', 'fail')
                return redirect(url_for('product.access_product', product_id=product_id))
            
            # Verifica disponibilità prodotto
            if product.availability == 0:
                flash('Prodotto non disponibile', 'fail')
                return redirect(url_for('product.access_product', product_id=product_id))
            profile = Profile.query.filter_by(id = session['current_profile_id']).first()

            for item in profile.cart_items:
                if item.product_id == product.id:
                    flash('Prodotto già presente nel carrello', 'fail')
                    return redirect(url_for('product.access_product', product_id=product_id))
                
            if not current_user.cards or not current_user.addresses:
                flash('Devi avere almeno una carta di credito e un indirizzo per poter continuare con l\'acquisto', 'FAIL')
                return redirect(url_for('product.access_product', product_id=product_id))
        except Exception as e:
            print(f"Errore durante l'operazione: {str(e)}")
            flash('Si è verificato un errore di database3. Riprova più tardi',"error")
            return redirect(url_for('product.access_product', product_id=product_id))
        
        return render_template('order_product.html', product = product)