from flask_login import LoginManager
from .database import User, db

login_manager = LoginManager()

# Settaggio del login_manager
# Quando un utente anonimo accede a una ruote col decoratore @login_required,
# allora viene rimandato alla schermata di login_view con il messaggio login_message
login_manager.login_view = "auth.login"
login_manager.login_message = "To access, you have to log in."
login_manager.login_message_category = "info"

# Settaggio del login_manager
# Quando un utente anonimo accede a una ruote col decoratore @login_required,
# allora viene rimandato alla schermata di refresh_view con il messaggio login_message
login_manager.refresh_view = "auth.login"
login_manager.needs_refresh_message = "To protect your account, please reauthenticate to access this page."
login_manager.needs_refresh_message_category = "info"

# Serve a ricaricare l'oggetto utente usando lo user.id
# Usato internamente da Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,int(user_id)) #User.query.get(int(user_id)) è considerato legacy