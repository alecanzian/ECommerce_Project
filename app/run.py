from extensions.flask import app
from extensions.princ import princ
from extensions.login import login_manager
from extensions.limiter import limiter
from extensions.database import db, popolate_db

# Inizializzo i moduli
db.init_app(app)
login_manager.init_app(app)
princ.init_app(app)
limiter.init_app(app)

if __name__ == '__main__':
    with app.app_context():
        #popolate_db() # Resetto e creo un nuovo db con dati di esempio
        pass
    app.run(debug=True)