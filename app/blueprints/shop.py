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
    try:
        # Visto che ci sono tre controlli, ovvero la barra di ricerca, il checkbox e il range di prezzo, ho bisogno di salvarmi ciò che visualizza l'utente.
        if 'selected_products' not in session:
            # Se current_user è un seller, devo togliere tutti i prodotti venduti da lui dai prodotti visibili sullo shop
            if current_user.is_authenticated:
                if current_user.has_role('seller'):
                    session['selected_products'] = [p.id for p in Product.query.filter(Product.user_id != current_user.id).all()]
                else:
                    session['selected_products'] = [p.id for p in Product.query.all()]
            else:
                session['selected_products'] = [p.id for p in Product.query.all()]

        # I prodotti il cui id è presente nella sessione. Questo perchè potrebbe esserci una route che reindirizza a shop e session['selected_products'] potrebbe averedegli elementi
        products = Product.query.filter(Product.id.in_(session['selected_products'])).all()
                
    except Exception:
        flash('Si è verificato un errore di database. Riprova più tardi','ERROR')
        return redirect(url_for('auth.logout'))
    
    if 'selected_categories' not in session:
        session['selected_categories'] = []
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
        selected_categories = request.form.getlist('selected_categories') # lista delle categorie selezionate
        min_price = float(request.form.get('minPriceRange', 0)) # prezzo minimo
        max_price = float(request.form.get('maxPriceRange', 6000)) # prezzo massimo

        # Aggiorno i valori corrispondenti alle chiavi 
        session['min_price'] = min_price
        session['max_price'] = max_price
        session['selected_categories'] = selected_categories

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
            if selected_categories:
                products = products.filter(Product.categories.any(Category.name.in_(selected_categories)))

            # I prodotti che rispettano che corrispondono a quelli precedenti e filtrati in base al prezzo
            products = products.filter(Product.price >= min_price, Product.price <= max_price).all()

            # Aggiorno gli id dei prodotti
            session['selected_products'] = [p.id for p in products]
        except Exception:
            flash('Si è verificato un errore di database. Riprova più tardi','ERROR')
            return redirect(url_for('auth.logout'))

        return render_template('homepage.html', products=products, categories=Category.query.all())

@app.route('/reset_filters', methods=['GET'])
#@login_required
#@buyer_required
def reset_filters():
    # Rimuovi tutte le categorie selezionate dalla sessione
    session['selected_categories'] = []

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
        flash('Si è verificato un errore di database. Riprova più tardi','ERROR')
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