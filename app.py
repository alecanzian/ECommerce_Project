from datetime import timedelta
from flask import Flask, render_template, session, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
#from flask_login import UserMixin
#from flask_wtf import wtforms
#from wtforms import StringField, PasswordField, SubmitField
#from wtforms.validators import InputRequired, Length, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash



db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/utente/Desktop/UNIVE/vsc/BD/dbms.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=20)  # Imposta la durata della sessione a 20 minuti
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(20), nullable = False)
        password = db.Column(db.String(80), nullable = False)

        def __init__(self, username, password):
                self.username = username
                self.password = password

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __init__(self, name, price):
        self.name = name
        self.price = price

@app.route('/')
def home():
        return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
        error_message = ""
        if request.method == 'POST':
                username = request.form['email']
                password = request.form['password']
                user = User.query.filter_by(username=username).first()
                if user:
                        if check_password_hash(user.password, password):
                                session['username'] = username
                                flash('Login successful!', category='success')
                                return redirect(url_for('shop'))
                        else:
                                #flash('Incorrect password.', category='error')
                                error_message = "Incorrect password."
                else:
                        #flash('Login failed. Check your email and password.', category='error')
                        error_message = "Login failed. Check your email and password."
        return render_template('login.html', error_message=error_message)

@app.route('/register', methods=['GET', 'POST'])
def register():
        if request.method == 'POST':
                username = request.form['email']
                password = request.form['password']
                confirm_password = request.form['confirm_password']

                # Controllo se l'username esiste già
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                        flash('Username already exists. Please login.', category='error')
                        return redirect(url_for('login'))

                if password != confirm_password:
                        flash('Passwords do not match!', category='error')
                else:
                        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                        new_user = User(username=username, password=hashed_password)
                        try:
                                db.session.add(new_user)
                                db.session.commit()
                                print("User registered successfully.")  # Log per il debugging
                                flash('Registration successful!', category='success')
                                return redirect(url_for('login'))
                        except Exception as e:
                                db.session.rollback()
                                print(f"Error occurred: {e}")  # Log per il debugging
                                flash('An error occurred during registration. Please try again.', category='error')
                                return redirect(url_for('register'))
        return render_template('register.html')

@app.route('/info')
def info():
        all_users = User.query.all()
        all_products = Products.query.all()
        return render_template('info.html', users=all_users, products = all_products)

@app.route('/shop')
def shop():
    products = Products.query.all()
    return render_template('shop.html', products=products)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logout avvenuto con successo!', category='success')
    return redirect(url_for('home'))
        

if __name__ == '__main__':
        with app.app_context():
                db.create_all()  # Creazione delle tabelle nel database
                #example_products = [
                #Products(name='Scarpe Nike', price=10.99),
                #Products(name='Jeans Levis', price=19.99),
                #Products(name='Occhiali da sole H. Boss', price=15.49)
                #]
                ## Aggiungi i prodotti al database
                #db.session.add_all(example_products)
                #db.session.commit()
                #example_users = [
                #User(username='alessandrocanzian2003@gmail.com', password=generate_password_hash('alex', method='pbkdf2:sha256')),
                #User(username='canzianpaolo2000@gmail.com', password=generate_password_hash('pp66', method='pbkdf2:sha256')),
                #User(username='giorgiaspigariol@gmail.com', password=generate_password_hash('bababa', method='pbkdf2:sha256'))
                #]
                ## Aggiungi i prodotti al database
                #db.session.add_all(example_users)
                #db.session.commit()
        app.run(debug = True)