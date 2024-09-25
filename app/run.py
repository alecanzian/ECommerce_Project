from extensions.flask import app
from extensions.princ import princ
from extensions.login import login_manager
from extensions.limiter import limiter
#from extensions.database import db, Address, Product, add_categories, add_roles, set_user_with_role, add_products, generate_password_hash, User, Profile
from extensions.database import *

# Inizializzo moduli
db.init_app(app)
login_manager.init_app(app)
princ.init_app(app)
limiter.init_app(app)

if __name__ == '__main__':
    with app.app_context():
        #db.drop_all() # Elimina tutte le tabelle nel database
        db.create_all()  # Crea tutte le tabelle nel database
        #add_roles()  # Popola il database con ruoli di esempio
        #add_states()
        #
        #example_categories = ['Elettronica','Abbigliamento','Casa e Giardino','Sport e Tempo Libero','Giochi e Giocattoli','Alimentari','Libri e Riviste','Salute e Bellezza','Arredamento','Auto e Moto','Fai da te','Musica','Film e TV','Animali domestici','Strumenti Musicali','Telefonia','Arte e Collezionismo','Viaggi','Tecnologia','Orologi e Gioielli','Altro']
        #add_categories(example_categories)
        #
        #user = User(username = 'admin@admin.com', password = generate_password_hash('admin', method='pbkdf2:sha256') )
        #db.session.add(user)
        #db.session.commit()
        #
        #db.session.add(Profile(name = 'Admin', surname = 'Admin', birth_date=datetime.strptime('2000-07-30', '%Y-%m-%d').date(), user_id=user.id))
        #db.session.commit()
        #
        #example = User(username = 'canzianpaolo@gmail.com', password = generate_password_hash('paolo', method='pbkdf2:sha256') )
        #db.session.add(example)
        #db.session.commit()
        #db.session.add(Profile(name = 'Paolo', surname = 'Canzian', birth_date=datetime.strptime('1966-05-11', '%Y-%m-%d').date(), user_id=example.id))
        #db.session.commit()
        #
        #addr = Address(street = 'Via borgo san andrea 85', postal_code = 31050, city = 'Povegliano', province = 'TV', country = 'Italia', user_id = user.id)
        #db.session.add(addr)
        #db.session.commit()
        #addr2 = Address(street = 'Via borgo san andrea 85', postal_code = 31050, city = 'Povegliano', province = 'TV', country = 'Italia', user_id = example.id)
        #db.session.add(addr2)
        #db.session.commit()
        #card1 = Card( name = 'alessandro', surname = 'canzian', pan= '1234567890987890', last_digits = '7890', expiration_month = '11', expiration_year= '2024', card_type = 'credit', user_id = example.id)
        #db.session.add(card1)
        #db.session.commit()
        #card1 = Card( name = 'paolo', surname = 'canzian', pan= '1872567890981234', last_digits = '1234', expiration_month = '12', expiration_year= '2032', card_type = 'credit', user_id = user.id)
        #db.session.add(card1)
        #db.session.commit()
        #
        ##db.session.add(Address(street = 'Via borgo san andrea 85', postal_code = 31050, city = 'Povegliano', province = 'TV', country = 'Italia', user_id = example.id))
        #
        #set_user_with_role(user, 'admin')  # Aggiungi un utente di esempio
        #set_user_with_role(user, 'buyer')  # Aggiungi un utente di esempio
        #set_user_with_role(user, 'seller')  # Aggiungi un utente di esempio
        #example_products = [
        #    {"name": "Scarpe Nike", "price": 10.99, "description": "gnegne", "availability": 10, "category": "Sport e Tempo Libero"},
        #    {"name": "Jeans Levis", "price": 19.99, "description": "gnegne", "availability": 2, "category": "Abbigliamento"},
        #    {"name": "Occhiali da sole H. Boss", "price": 15.49, "description": "gnegne", "availability": 5, "category": "Salute e Bellezza"},
        #    {"name": "Laptop Dell", "price": 499.99, "description": "Laptop ad alte prestazioni", "availability": 3, "category": "Elettronica"},
        #    {"name": "Smartphone Samsung", "price": 299.99, "description": "Smartphone di ultima generazione", "availability": 15, "category": "Telefonia"},
        #    {"name": "Divano Ikea", "price": 199.99, "description": "Divano confortevole e moderno", "availability": 4, "category": "Arredamento"},
        #    {"name": "Trapano Bosch", "price": 89.99, "description": "Trapano per lavori di fai da te", "availability": 12, "category": "Fai da te"},
        #    {"name": "Romanzo di Dan Brown", "price": 12.99, "description": "Thriller avvincente", "availability": 20, "category": "Libri e Riviste"},
        #    {"name": "Chitarra Fender", "price": 249.99, "description": "Chitarra elettrica per musicisti", "availability": 2, "category": "Musica"},
        #    {"name": "Orologio Rolex", "price": 4999.99, "description": "Orologio di lusso", "availability": 1, "category": "Orologi e Gioielli"},
        #    {"name": "Videogioco PS5", "price": 59.99, "description": "Videogioco di ultima generazione", "availability": 30, "category": "Giochi e Giocattoli"},
        #    {"name": "Cibo per cani", "price": 24.99, "description": "Alimento completo per cani", "availability": 50, "category": "Alimentari"},
        #    {"name": "Set di pentole", "price": 79.99, "description": "Set di pentole antiaderenti", "availability": 10, "category": "Casa e Giardino"}
        #]
        #
        #add_products(example_products)
    app.run(debug=True)