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
        #popolate_db()
        pass
    app.run(debug=True)