from flask import Blueprint, render_template, session, redirect, request, url_for
from flask_login import login_required, current_user
from extensions.database import Profile, Product, Category, db
from extensions.princ import buyer_required, seller_required

app = Blueprint('shop', __name__)

@app.route('/shop')
@login_required
@buyer_required
def shop():
    if 'current_profile_id' not in session:
        return redirect(url_for('profile.profile_selection'))
    
    # Visto che ci sono tre controlli, ovvero la barra di ricerca, il checkbox e il range di prezzo, ho bisogno di salvarmi ciò che visualizza l'utente.
    if 'selected_products' not in session:
        # Se current_user è un seller, devo togliere tutti i prodotti venduti da lui dai prodotti visibili sullo shop
        if current_user.has_role('seller'):
            #user_profile_ids = [p.id for p in current_user.profiles]
            session['selected_products'] = [p.id for p in Product.query.filter(Product.user_id != current_user.id).all()]
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

    return render_template('shop.html', products=products, categories=Category.query.all()) 

@app.route('/filtered_results', methods=['POST'])
@login_required
@buyer_required
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


        # Aggiorna la sessione con gli ID dei prodotti visibili,tranne quelli che appartengono a current_user
        if current_user.has_role('seller'):
            #user_profile_ids = [p.id for p in current_user.profiles]
            #session['selected_products'] = [p.id for p in Product.query.filter(~Product.profile_id.in_(user_profile_ids)).all()]
            session['selected_products'] = [p.id for p in Product.query.filter(Product.user_id != current_user.id).all()]
        else:
            session['selected_products'] = [p.id for p in Product.query.all()]

        # Ritorna alla pagina shop con i prodotti e categorie aggiornati
        return redirect(url_for('shop.shop'))
    
@app.route('/cart')
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

# PARTE AGGIUNTIVA(ancora da fare)


@app.route('/create_product')
@login_required
@seller_required
def create_product():
    return render_template('create_product.html', categories = Category.query.all())

@app.route('/add_product', methods=['POST'])
@login_required
@seller_required
def add_product():
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
    user_id = current_user.id

    
    if image_url is None:
        new_product = Product(name=name, price=price, user_id=user_id, description = description, availability = availability, categories = category_objects)
    else:
        new_product = Product(name=name, price=price, user_id=user_id, description = description, availability = availability, categories = category_objects, image_url = image_url)
    db.session.add(new_product)
    db.session.commit()
    return redirect(url_for('profile.profile'))