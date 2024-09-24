from flask import Blueprint, flash, render_template, session, redirect, request, url_for
from flask_login import login_required, current_user
from flask_migrate import current
from extensions.database import Cart, Notification, Order, OrderProduct, Profile, State, db, Product, Category, get_user_orders#, Order
from extensions.princ import buyer_required, seller_required

app = Blueprint('shop', __name__)

@app.route('/homepage', methods = ['GET'])
def homepage():
    return redirect(url_for('shop.shop'))

@app.route('/shop', methods = ['GET'])
#@login_required
#@buyer_required
def shop():
    if current_user.is_authenticated:
        if 'current_profile_id' not in session:
            flash('Seleziona prima un profilo', 'ERROR')
            return redirect(url_for('profile.select'))
    try:
        if current_user.is_authenticated:
        # Visto che ci sono tre controlli, ovvero la barra di ricerca, il checkbox e il range di prezzo, ho bisogno di salvarmi ciò che visualizza l'utente.
            if 'selected_products' not in session:
                flash('selected_products non eisste', 'Error')
                return redirect(url_for('auth.logout'))
            print('selected_products esiste')
            # Se current_user è un seller, devo togliere tutti i prodotti venduti da lui dai prodotti visibili sullo shop
            if current_user.has_role('seller'):
                # Recupera i prodotti che non appartengono all'utente corrente
                not_seller_products = [p.id for p in Product.query.filter(Product.user_id != current_user.id).all()]

                # Recupera i prodotti precedentemente salvati nella sessione
                session_products = session.get('selected_products', [])

                # Calcola l'intersezione tra i prodotti della sessione e quelli che non appartengono all'utente corrente
                selected_intersection = list(set(session_products) & set(not_seller_products))

                # Aggiorna la sessione con i prodotti intersecati
                session['selected_products'] = selected_intersection

                
        else:
            if 'selected_products' not in session:
                session['selected_products'] = [p.id for p in Product.query.all()]
                
        # I prodotti il cui id è presente nella sessione. Questo perchè potrebbe esserci una route che reindirizza a shop e session['selected_products'] potrebbe averedegli elementi
        products = Product.query.filter(Product.id.in_(session['selected_products'])).all()
                
    except Exception as e:
        print(e)
        flash('Si è verificato un errore di database. Riprova più tardi',"error")
        return redirect(url_for('auth.logout'))
    
    if current_user.is_authenticated:
        if 'selected_category_name' not in session:
            session['selected_category_name'] = ''
    else:
        session['selected_category_name'] = ''
    if 'min_price' not in session:
        session['min_price'] = 0.0
    if 'max_price' not in session:
        session['max_price'] = 6000.0
    return render_template('homepage.html', products=products, categories=Category.query.all()) 

@app.route('/filtered_results', methods=['POST'])
#@login_required
#@buyer_required
def filtered_results():
    if request.method == 'POST':
        # Estrapolo tutte le informazioni necessarie dal form
        query = request.form.get('query', '') # query della barra di ricerca
        category_name = request.form.get('selected_category_name') # lista delle categorie selezionate
        min_price = float(request.form.get('minPriceRange', 0)) # prezzo minimo
        max_price = float(request.form.get('maxPriceRange', 6000)) # prezzo massimo

        # Aggiorno i valori corrispondenti alle chiavi 
        session['min_price'] = min_price
        session['max_price'] = max_price
        session['selected_category_name'] = category_name

        try:
            # Filtra i prodotti in base ai criteri
            products = Product.query

            # Escludi i prodotti che appartengono ai profili di current_user, se current_user è un seller
            if current_user.is_authenticated:
                if current_user.has_role('seller'):
                    products = products.filter(Product.user_id != current_user.id)

            # Se la query non è una stringa vuota
            if query:
                products = products.filter(Product.name.ilike(f'%{query}%'))

            # Se ci sono delle categorie selezionate
            if category_name:
                products = products.filter(Product.category.has(Category.name == category_name))

            # I prodotti che rispettano che corrispondono a quelli precedenti e filtrati in base al prezzo
            products = products.filter(Product.price >= min_price, Product.price <= max_price).all()

            # Aggiorno gli id dei prodotti
            session['selected_products'] = [p.id for p in products]
        except Exception as e:
            print(e)
            flash('Si è verificato un errore di database. Riprova più tardi',"error")
            return redirect(url_for('auth.logout'))

        return render_template('homepage.html', products=products, categories=Category.query.all())

@app.route('/reset_filters', methods=['GET'])
#@login_required
#@buyer_required
def reset_filters():
    # Rimuovi tutte le categorie selezionate dalla sessione
    session['selected_category_name'] = ''

    # Reimposta i valori di min_price e max_price nella sessione
    session['min_price'] = 0.0
    session['max_price'] = 6000.0

    try:
        # Aggiorna la sessione con gli ID dei prodotti visibili,tranne quelli che appartengono a current_user
        if current_user.is_authenticated:
            if current_user.has_role('seller'):
                session['selected_products'] = [p.id for p in Product.query.filter(Product.user_id != current_user.id).all()]
            else:
                session['selected_products'] = [p.id for p in Product.query.all()]
        else:
            session['selected_products'] = [p.id for p in Product.query.all()]
    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi',"error")
        return redirect(url_for('auth.logout'))

    # Ritorna alla pagina shop con i prodotti e categorie aggiornati
    return redirect(url_for('shop.shop'))
    
@app.route('/orders', methods = ['GET'])
@login_required
def orders():
    return render_template('orders.html')

@app.route('/modify_order_state/<int:order_product_id>', methods = ['GET', 'POST'])
@login_required
def modify_order_state(order_product_id):
    order_product = OrderProduct.query.filter_by(id = order_product_id).first()
    if not order_product or order_product.product.user_id != current_user.id:
        flash('order_product non trovato',"error")
        return redirect(url_for('account.view'))
    if request.method == 'POST':
        state_id = int(request.form.get('selected_state_id'))
        state = State.query.filter_by(id = state_id).first()
        if not state:
            flash('Stato non trovato',"error")
            return redirect(url_for('account.view'))
        order_product.state_id = state_id#mancano i controlli se esiste lo state_id

        new_notification = Notification(
            sender_id =  current_user.id,
            receiver_id = order_product.order.user_id,
            type = 'Stato ordine modificato',
            product_name = order_product.product.name,
            order_id = order_product.order_id
        )
        db.session.add(new_notification)
        db.session.commit()
        flash('Stato dell\'ordine modificato con successo', "success")
        return redirect(url_for('account.view'))
    
    consegnato_state = State.query.filter_by(name = 'Consegnato').first()
    if not consegnato_state:
        flash('Stato non trovato',"error")
        return redirect(url_for('account.view'))
    
    if order_product.state_id == consegnato_state.id:
        print(order_product.product_name)
        print(order_product.state_id)
        print(order_product.state.name)
        print(consegnato_state.id)
        print(consegnato_state.name)
        flash('non puoi cambiare lo stato dopo che è stato consegnato','fail')
        return redirect(url_for('account.view'))
    all_states = State.query.all()
    return render_template('modify_order_state.html', order_product = order_product, states = all_states)