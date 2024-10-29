from flask_login import LoginManager
from .database import User, db

login_manager = LoginManager()

# Configurazione del login_manager
# Quando un utente anonimo tenta di accedere a una rotta protetta dal decoratore @login_required,
# viene reindirizzato alla vista specificata in login_view con il messaggio login_message
login_manager.login_view = "auth.logout"
login_manager.login_message = "Per accedere, devi effettuare l'accesso."
login_manager.login_message_category = "error"

# Configurazione del login_manager per la richiesta di reautenticazione
# Quando un utente anonimo tenta di accedere a una rotta che richiede una reautenticazione,
# viene reindirizzato alla vista specificata in refresh_view con il messaggio needs_refresh_message
login_manager.refresh_view = "auth.logout"
login_manager.needs_refresh_message = "Per proteggere il tuo account, per favore riautenticati per accedere a questa pagina."
login_manager.needs_refresh_message_category = "error"

# Serve a ricaricare l'oggetto utente usando lo user.id
# Usato internamente da Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User,int(user_id)) 
    except Exception:
        return None