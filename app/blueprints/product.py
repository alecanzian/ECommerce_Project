from flask import Blueprint, flash, render_template, session, redirect, request, url_for
from flask_login import login_required, current_user
from extensions.database import Cart, Order, OrderProduct, Profile, db, Product, Category, get_user_orders#, Order
from extensions.princ import buyer_required, seller_required

app = Blueprint('product', __name__)

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
                    return redirect(url_for('product.modify_product', product_id=product.id))
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

@app.route('/order_product/<int:product_id>',methods = ['GET', 'POST'])
@login_required
def order_product(product_id):
    if request.method == 'POST':
        quantity = int(request.form.get('quantity'))
        address_id = int(request.form.get('selected_address_id'))
        # Verifica preliminare della quantità e indirizzo
        if not quantity or not address_id:
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

        except Exception:
            flash('Si è verificato un errore di database1. Riprova più tardi.', 'error')
            return redirect(url_for('product.access_product', product_id=product_id))

        
        # Operazioni critiche sul database in blocco try-except
        try:
            profile = Profile.query.filter_by(id = session['current_profile_id']).first()
            if not profile:
                 flash('Profilo non trovato', 'fail')
                 return redirect(url_for('product.access_product', product_id=product_id))
            # Creazione del nuovo ordine
            address_name = address.street + ", " + str(address.postal_code) +", " + address.city + ", " + address.province + ", " + address.country
            new_order = Order(user_id = current_user.id, profile_id = profile.id, profile_name = profile.name, address = address_name, total_price = (product.price * quantity))
            db.session.add(new_order)
            db.session.flush()  # Forza la generazione dell'ID per l'ordine

            # Aggiungi il prodotto all'ordine
            new_order_product = OrderProduct(order_id=new_order.id, product_id=product.id, product_name = product.name, quantity=quantity)
            
            db.session.add(new_order_product)
            product.availability-=quantity
            db.session.commit()
            flash('Ordine effettuato con successo', 'success')
            return redirect(url_for('shop.orders'))

        except Exception as e:
            # In caso di errore, rollback e gestione dell'eccezione
            db.session.rollback()
            print(f"Errore durante l'operazione: {str(e)}")
            flash('Si è verificato un errore di database2. Riprova più tardi.', 'error')
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

            for item in current_user.cart_items:
                if item.product_id == product.id:
                    flash('Prodotto già presente nel carrello', 'fail')
                    return redirect(url_for('product.access_product', product_id=product_id))
        except Exception as e:
            print(f"Errore durante l'operazione: {str(e)}")
            flash('Si è verificato un errore di database3. Riprova più tardi','error')
            return redirect(url_for('product.access_product', product_id=product_id))
        
        return render_template('order_product.html', product = product)