from flask import Blueprint, flash, render_template, session, redirect, request, url_for
from flask_login import login_required, current_user
from extensions.database import Cart, Order, OrderProduct, Profile, State, db, Product, Category, get_user_orders#, Order
from extensions.princ import buyer_required, seller_required

app = Blueprint('shop', __name__)

@app.route('/shop', methods = ['GET'])
#@login_required
#@buyer_required
def shop():
    if current_user.is_authenticated:
        if 'current_profile_id' not in session:
            return redirect(url_for('profile.profile_selection'))
    
    # Visto che ci sono tre controlli, ovvero la barra di ricerca, il checkbox e il range di prezzo, ho bisogno di salvarmi ciò che visualizza l'utente.
    if 'selected_products' not in session:
        # Se current_user è un seller, devo togliere tutti i prodotti venduti da lui dai prodotti visibili sullo shop
        if current_user.is_authenticated:
            if current_user.has_role('seller'):
                #user_profile_ids = [p.id for p in current_user.profiles]
                session['selected_products'] = [p.id for p in Product.query.filter(Product.user_id != current_user.id).all()]
            else:
                session['selected_products'] = [p.id for p in Product.query.all()]
        else:
            session['selected_products'] = [p.id for p in Product.query.all()]

    if 'selected_categories' not in session:
        session['selected_categories'] = []
    if 'min_price' not in session:
        session['min_price'] = 0.0
    if 'max_price' not in session:
        session['max_price'] = 6000.0
    
    # I prodotti il cui id è presente nella sessione. Questo perchè potrebbe esserci una route che reindirizza a shop e session['selected_products'] potrebbe averedegli elementi
    products = Product.query.filter(Product.id.in_(session['selected_products'])).all()

    return render_template('homepage.html', products=products, categories=Category.query.all()) 

@app.route('/filtered_results', methods=['POST'])
#@login_required
#@buyer_required
def filtered_results():
    if request.method == 'POST':
        # Estrapolo tutte le informazioni necessarie dal form
        query = request.form.get('query', '') # query della barra di ricerca
        selected_categories = request.form.getlist('selected_categories') # lista delle categorie selezionate
        min_price = float(request.form.get('minPriceRange', 0)) # prezzo minimo
        max_price = float(request.form.get('maxPriceRange', 6000)) # prezzo massimo

        # Aggiorno i valori corrispondenti alle chiavi 
        session['min_price'] = min_price
        session['max_price'] = max_price
        session['selected_categories'] = selected_categories

        # Filtra i prodotti in base ai criteri
        products = Product.query

        # Escludi i prodotti che appartengono ai profili di current_user, se current_user è un seller
        if current_user.is_authenticated:
            if current_user.has_role('seller'):
                #user_profile_ids = [p.id for p in current_user.profiles]
                #products = products.filter(~Product.profile_id.in_(user_profile_ids))
                products = products.filter(Product.user_id != current_user.id)

        # Se la query non è una stringa vuota
        if query:
            products = products.filter(Product.name.ilike(f'%{query}%'))

        # Se ci sono delle categorie selezionate
        if selected_categories:
            products = products.filter(Product.categories.any(Category.name.in_(selected_categories)))

        # I prodotti che rispettano che corrispondono a quelli precedenti e filtrati in base al prezzo
        products = products.filter(Product.price >= min_price, Product.price <= max_price).all()

        # Aggiorno gli id dei prodotti
        session['selected_products'] = [p.id for p in products]

        return render_template('homepage.html', products=products, categories=Category.query.all())

@app.route('/reset_filters', methods=['POST'])
#@login_required
#@buyer_required
def reset_filters():
    if request.method == 'POST':
        # Rimuovi tutte le categorie selezionate dalla sessione
        session['selected_categories'] = []

        # Reimposta i valori di min_price e max_price nella sessione
        session['min_price'] = 0.0
        session['max_price'] = 6000.0

        # Aggiorna la sessione con gli ID dei prodotti visibili,tranne quelli che appartengono a current_user
        if current_user.is_authenticated:
            if current_user.has_role('seller'):
                #user_profile_ids = [p.id for p in current_user.profiles]
                #session['selected_products'] = [p.id for p in Product.query.filter(~Product.profile_id.in_(user_profile_ids)).all()]
                session['selected_products'] = [p.id for p in Product.query.filter(Product.user_id != current_user.id).all()]
            else:
                session['selected_products'] = [p.id for p in Product.query.all()]
        else:
            session['selected_products'] = [p.id for p in Product.query.all()]

        # Ritorna alla pagina shop con i prodotti e categorie aggiornati
        return redirect(url_for('shop.shop'))
    
@app.route('/cart', methods = ['GET'])
@login_required
@buyer_required
def cart():
    return render_template('cart.html')



@app.route('/product/<int:product_id>')
@login_required
@buyer_required
def access_product(product_id):
    product = Product.query.get_or_404(product_id)
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
        list_categories = request.form.getlist('selected_categories_product')
        category_objects = []
        for category_name in list_categories:
                        category = Category.query.filter_by(name=category_name).first()
                        if not category:
                            category = Category.query.filter_by(name='Altro').first()
                        category_objects.append(category)
        if not category_objects:
            category_objects.append(Category.query.filter_by(name='Altro').first())
        user_id = current_user.id

        
        if image_url == "":
            new_product = Product(name=name, price=price, user_id=user_id, description = description, availability = availability, categories = category_objects)
        else:
            new_product = Product(name=name, price=price, user_id=user_id, description = description, availability = availability, categories = category_objects, image_url = image_url)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('profile.profile'))
    
    return render_template('add_product.html', categories = Category.query.all())


@app.route('/delete_product/<int:product_id>', methods = ['GET', 'POST'])
@login_required
@seller_required
def delete_product(product_id):
    product = next((p for p in current_user.products if p.id == product_id), None)
   
    if product:
        # Elimino tutte le tuple del carrello che si riferiscono a quell'oggetto
        for item in product.in_carts:
            db.session.delete(item)
        db.session.delete(product)
        db.session.commit()
        flash('Prodotto eliminato correttamente', 'message')
        return redirect(url_for('profile.profile'))
    else:
        flash('il prodotto non è stato trovato', 'error')
        return redirect(url_for('profile.profile'))
    
@app.route('/modify_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def modify_product(product_id):
    product = next((p for p in current_user.products if p.id == product_id), None)
    if not product:
        flash('il prodotto non è stato trovato', 'error')
        return redirect(url_for('profile.profile'))

    if request.method == 'POST':
        # Leggi i dati inviati dal form
        name = request.form.get('name')
        price = request.form.get('price')
        image_url = request.form.get('image_url')
        description = request.form.get('description')
        availability = request.form.get('availability')
        list_categories = request.form.getlist('selected_categories_product')
        categories = []
        for category_name in list_categories:
                        category = Category.query.filter_by(name=category_name).first()
                        if not category:
                            category = Category.query.filter_by(name='Altro').first()
                        categories.append(category)
        if not categories:
            categories.append(Category.query.filter_by(name='Altro').first())
        
        if name:
            for p in current_user.products:
                if p.id != product.id and name == p.name:
                    flash('Nome già utilizzato')
                    return redirect(url_for('shop.modify_product', product_id=product.id))
            product.name = name
            
        if price:
            product.price = price

        if description:
            product.description = description
            
        if image_url:
            product.image_url = image_url
            
        if availability:
            product.availability = availability
            print("prodotto ha disponibilità aggiornata")
            if int(availability) == 0:
                for item in product.in_carts:
                    db.session.delete(item)
                print("prodotto ha disponibilità 0")
           
        db.session.commit()
        flash('Prodotto aggiornato con successo')
        return redirect(url_for('profile.profile'))
    
    return render_template('modify_product.html', product=product, categories = Category.query.all())

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
    flash('Prodotto aggiunto correttamente al carrello', 'success')
    return redirect(url_for('product.access_product', product_id=product_id))

@app.route('/delete_item_from_cart/<int:item_id>', methods = ['GET'])
@login_required
def delete_item_from_cart(item_id):
    item = next((item for item in current_user.cart_items if item.id == item_id), None)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Prodotto rimosso correttamente dal carrello', 'success')
        return redirect(url_for('shop.cart'))
    flash('Prodotto non trovato nel carrello', 'error')
    return redirect(url_for('shop.cart'))


@app.route('/orders', methods = ['GET'])
@login_required
def orders():
    return render_template('orders.html')

@app.route('/modify_order_state/<int:order_product_id>', methods = ['GET', 'POST'])
@login_required
def modify_order_state(order_product_id):
    order_product = OrderProduct.query.filter_by(id = order_product_id).first()
    if not order_product:
        flash('order_product non trovato','error')
        return redirect(url_for('profile.profile'))
    if request.method == 'POST':
        state_id = int(request.form.get('selected_state_id'))
        state = State.query.filter_by(id = state_id).first()
        if not state:
            flash('Stato non trovato','error')
            return redirect(url_for('profile.profile'))
        order_product.state_id = state_id#mancano i controlli se esiste lo state_id
        db.session.commit()
        flash('Stato dell\'ordine modificato con successo', 'success')
        return redirect(url_for('profile.profile'))
    
    consegnato_state = State.query.filter_by(name = 'Consegnato').first()
    if not consegnato_state:
        flash('Stato non trovato','error')
        return redirect(url_for('profile.profile'))
    
    if order_product.state_id != consegnato_state.id:
        print(order_product.product_name)
        print(order_product.state_id)
        print(order_product.state.name)
        print(consegnato_state.id)
        print(consegnato_state.name)
        flash('non puoi cambiare lo stato dopo che è stato consegnato','fail')
        return redirect(url_for('profile.profile'))
    all_states = State.query.all()
    return render_template('modify_order_state.html', order_product = order_product, states = all_states)

@app.route('/homepage', methods = ['GET'])
def homepage():
    return render_template('homepage.html')

@app.route('/order_cart_items', methods = ['GET', 'POST'])
@login_required
def order_cart_items():
    if request.method == 'POST':
        address_id = int(request.form.get('selected_address_id'))
        if not address_id:
            flash('Indirizzo non valido', 'fail')
            return redirect(url_for('shop.order_cart_items'))
        try:
            address = next((address for address in current_user.addresses if address.id == address_id),None)
            if not address:
                flash('Indirizzo non trovato', 'fail')
                return redirect(url_for('shop.order_cart_items'))
            items = current_user.cart_items
            if not items:
                flash('Carrello vuoto', 'fail')
                return redirect(url_for('shop.shop'))
            
            profile = Profile.query.filter_by(id = session['current_profile_id']).first()
            if not profile:
                 flash('Profilo non trovato', 'fail')
                 return redirect(url_for('shop.cart'))
            address = address.street + ", " + str(address.postal_code) +", " + address.city + ", " + address.province + ", " + address.country
            new_order = Order(user_id = current_user.id, profile_id = profile.id, profile_name = profile.name, address = address, total_price = 0.0)
            db.session.add(new_order)
            db.session.flush()

            total_price = 0.0
            for item in items:
                total_price += item.product.price * item.quantity
                new_order_product = OrderProduct(order_id = new_order.id, product_id = item.product_id, product_name = item.product.name, quantity = item.quantity)
                db.session.add(new_order_product)
                item.product.availability-=item.quantity
                db.session.delete(item)
            new_order.total_price = total_price

            db.session.commit()
            flash('Ordine avvenuto correttamente','success')
            return redirect(url_for('shop.orders'))
        except Exception as e:
            print(f"Errore durante l'operazione: {str(e)}")
            db.session.rollback()
            flash('Si è verificato un errore di database4. Riprova più tardi','error')
            return redirect(url_for('shop.cart'))
    return render_template('order_cart_items.html')

@app.route('/change_quantity_cart_item/<int:item_id>', methods = ['POST'])
@login_required
def change_quantity_cart_item(item_id):
    quantity = int(request.form.get('quantity'))
    if not quantity:
        flash('Inserisci la quantità prima di premere Applica', 'fail')
        return redirect(url_for('shop.cart'))
    try:
        item = next((i for i in current_user.cart_items if i.id == item_id), None)
        if not item:
            flash('Prodotto non trovato', 'error')
            return redirect(url_for('shop.cart'))
        item.quantity = quantity
        db.session.commit()
        flash('La quantità è stata aggiornata correttamente', 'success')
        return redirect(url_for('shop.cart'))
    except Exception as e:
        db.session.rollback()
        print(f"Errore durante l'operazione: {str(e)}")
        flash('Si è verificato un errore di database5. Riprova più tardi','error')
        return redirect(url_for('shop.cart'))