from flask import Flask
from extensions.database import db
from blueprints.auth import app as auth_bp
from blueprints.profile import app as profile_bp
from blueprints.shop import app as shop_bp
from blueprints.account import app as account_bp
from datetime import timedelta

# Configurazione Flask
app = Flask(__name__, static_folder='../static', template_folder='../templates')

app.secret_key = 'thisisasecretkey'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dbms.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:unive2024@ermen.ddns.net:5432/ermen'
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = db
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=40)  # Imposta la durata della sessione a 40 minuti

# Registra i blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(account_bp)