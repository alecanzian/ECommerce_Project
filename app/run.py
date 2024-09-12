from extensions.flask import app
from extensions.login import login_manager
from extensions.princ import princ
from extensions.database import Address, add_categories, add_roles, db, add_users, set_user_with_role, add_products, generate_password_hash, User, Profile
from datetime import datetime, timedelta
import os

# Configurazione per la sessione server-side
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dbms.db')
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = db
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=40)  # Imposta la durata della sessione a 20 minuti

login_manager.init_app(app)
princ.init_app(app)
db.init_app(app)
    
with app.app_context():
    db.create_all()  # Creazione delle tabelle nel database
    
    #add_roles()  # Popola il database con ruoli di esempio
    #
    #example_categories = ['Elettronica','Abbigliamento','Casa e Giardino','Sport e Tempo Libero','Giochi e Giocattoli','Alimentari','Libri e Riviste','Salute e Bellezza','Arredamento','Auto e Moto','Fai da te','Musica','Film e TV','Animali domestici','Strumenti Musicali','Telefonia','Arte e Collezionismo','Viaggi','Tecnologia','Orologi e Gioielli','Altro']
    #add_categories(example_categories)
    #
    #admin = User(username = 'alessandrocanzian2003@gmail.com', password = generate_password_hash('alex', method='pbkdf2:sha256') )
    #db.session.add(admin)
    #db.session.commit()
    #db.session.add(Profile(name = 'Alessandro', surname = 'Canzian', birth_date=datetime.strptime('2003-03-30', '%Y-%m-%d').date(), user_id=admin.id))
    #db.session.commit()
    #example = User(username = 'canzianpaolo@gmail.com', password = generate_password_hash('pp66', method='pbkdf2:sha256') )
    #db.session.add(example)
    #db.session.commit()
    #db.session.add(Profile(name = 'Paolo', surname = 'Canzian', birth_date=datetime.strptime('1966-05-11', '%Y-%m-%d').date(), user_id=example.id))
    #db.session.commit()
    #db.session.add(Address(street = 'Via borgo san andrea 85', postal_code = 31050, city = 'Povegliano', province = 'TV', country = 'Italia', user_id = admin.id))
    #db.session.add(Address(street = 'Via borgo san andrea 85', postal_code = 31050, city = 'Povegliano', province = 'TV', country = 'Italia', user_id = example.id))
    #db.session.commit()
    #
    #set_user_with_role('alessandrocanzian2003@gmail.com', 'admin')  # Aggiungi un utente di esempio
    #set_user_with_role('alessandrocanzian2003@gmail.com', 'buyer')  # Aggiungi un utente di esempio
    #set_user_with_role('alessandrocanzian2003@gmail.com', 'seller')  # Aggiungi un utente di esempio
    #
    #example_products = [
    #    {"name": "Scarpe Nike", "price": 10.99, "description": "gnegne", "availability": 10, "categories": ["Sport e Tempo Libero"]},
    #    {"name": "Jeans Levis", "price": 19.99, "description": "gnegne", "availability": 2, "categories": ["Abbigliamento"]},
    #    {"name": "Occhiali da sole H. Boss", "price": 15.49, "description": "gnegne", "availability": 5, "categories": ["Salute e Bellezza", "Abbigliamento"]},
    #    {"name": "Laptop Dell", "price": 499.99, "description": "Laptop ad alte prestazioni", "availability": 3, "categories": ["Elettronica", "Tecnologia"]},
    #    {"name": "Smartphone Samsung", "price": 299.99, "description": "Smartphone di ultima generazione", "availability": 15, "categories": ["Elettronica", "Telefonia"]},
    #    {"name": "Divano Ikea", "price": 199.99, "description": "Divano confortevole e moderno", "availability": 4, "categories": ["Casa e Giardino", "Arredamento"]},
    #    {"name": "Trapano Bosch", "price": 89.99, "description": "Trapano per lavori di fai da te", "availability": 12, "categories": ["Fai da te", "Tecnologia"]},
    #    {"name": "Romanzo di Dan Brown", "price": 12.99, "description": "Thriller avvincente", "availability": 20, "categories": ["Libri e Riviste"]},
    #    {"name": "Chitarra Fender", "price": 249.99, "description": "Chitarra elettrica per musicisti", "availability": 2, "categories": ["Strumenti Musicali", "Musica"]},
    #    {"name": "Orologio Rolex", "price": 4999.99, "description": "Orologio di lusso", "availability": 1, "categories": ["Orologi e Gioielli"]},
    #    {"name": "Videogioco PS5", "price": 59.99, "description": "Videogioco di ultima generazione", "availability": 30, "categories": ["Giochi e Giocattoli", "Tecnologia"]},
    #    {"name": "Cibo per cani", "price": 24.99, "description": "Alimento completo per cani", "availability": 50, "categories": ["Animali domestici", "Alimentari"]},
    #    {"name": "Set di pentole", "price": 79.99, "description": "Set di pentole antiaderenti", "availability": 10, "categories": ["Casa e Giardino", "Altro"]}
    #]
    #add_products(example_products)#
if __name__ == '__main__':
    app.run(debug=True)