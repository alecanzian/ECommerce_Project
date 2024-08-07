from flask import Blueprint, render_template, session, redirect, request, url_for
from flask_login import login_required, current_user
from extensions.database import Profile, Product, Category, db
from extensions.princ import buyer_required, seller_required

app = Blueprint('shop', __name__)

@app.route('/shop')
@login_required
def shop():
    # Inizializzazione di tutte le chiavi necessarie
    # Visto che ci sono tre controlli, ovvero la barra di ricerca, il checkbox e il range di prezzo, ho bisogno di salvarmi ciò che visualizza l'utente.
    if 'selected_products' not in session:
        session['selected_products'] = [p.id for p in Product.query.all()]
    if 'selected_categories' not in session:
        session['selected_categories'] = []
    if 'min_price' not in session:
        session['min_price'] = 0.0
    if 'max_price' not in session:
        session['max_price'] = 6000.0
    
    # I prodotti il cui id è presente nella sessione. Questo perchè potrebbe esserci una route che reindirizza a shop e session['selected_products'] potrebbe averedegli elementi
    products = Product.query.filter(Product.id.in_(session['selected_products'])).all()

    return render_template('shop.html', products=products, categories = Category.query.all()) 

@app.route('/filtered_results', methods=['POST'])
@login_required
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

        return render_template('shop.html', products=products, categories=Category.query.all())

@app.route('/reset_filters', methods=['POST'])
@login_required
@buyer_required
def reset_filters():
    if request.method == 'POST':
        # Rimuovi tutte le categorie selezionate dalla sessione
        session['selected_categories'] = []

        # Reimposta i valori di min_price e max_price nella sessione
        session['min_price'] = 0.0
        session['max_price'] = 6000.0

        # Reimposta i prodotti visibili utilizzando i filtri di default
        products = Product.query.all()

        # Aggiorna la sessione con gli ID dei prodotti visibili
        session['selected_products'] = [p.id for p in products]

        # Ritorna alla pagina shop con i prodotti e categorie aggiornati
        return redirect(url_for('shop.shop'))
    
@app.route('/cart')
@login_required
@buyer_required
def cart():
    return render_template('cart.html')

@app.route('/product/<int:product_id>')
@login_required
def access_product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

# PARTE AGGIUNTIVA(ancora da fare)

@app.route('/create_product', methods=['POST'])
@seller_required
def create_product():
    name = request.form.get('name')
    price = request.form.get('price')
    profile_id = request.form.get('profile_id')

    # Verifica se il profilo appartiene all'utente corrente
    profile = Profile.query.get(profile_id)
    if profile.user_id != current_user.id:
        return "Non hai il permesso di utilizzare questo profilo", 403

    new_product = Product(name=name, price=price, profile_id=profile_id)
    db.session.add(new_product)
    db.session.commit()
    return "Prodotto creato con successo", 201