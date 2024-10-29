from flask import flash, redirect, url_for, current_app
from flask_login import current_user
from flask_principal import Principal, Permission, RoleNeed, PermissionDenied, UserNeed, identity_loaded, identity_changed, Identity
from functools import wraps

princ = Principal()

# Definisce i permessi basati sui ruoli
admin_permission = Permission(RoleNeed('admin'))
seller_permission = Permission(RoleNeed('seller'))
buyer_permission = Permission(RoleNeed('buyer'))

# L'identità rappresenta l'utente e viene memorizzato/caricato per ogni richiesta
# Contiene i diritti di accesso dell'utente
@identity_loaded.connect
def on_identity_loaded(sender, identity):
    identity.user = current_user

    # Aggiunge l'id dell'user corrente all'identità
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Controlla se l'utente ha ruoli e li aggiunge all'identità per i permessi
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))
            
def update_identity(app, user_id):
    # Invia il segnale per aggiornare l'identità
    identity_changed.send(current_app._get_current_object(), identity=Identity(user_id))
    
# Decoratore personalizzato per gestire il caso in cui l'utente non ha l'autorizzazione(ovvero non possiede il ruolo) per eseguire una azione
def anonymous_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            flash('Devi prima eseguire il log out', 'error')
            return redirect(url_for('auth.logout'))  # Redirige alla home se l'utente è loggato
        return f(*args, **kwargs)
    return decorated_function

# Decoratore personalizzato per gestire il caso in cui l'utente non ha l'autorizzazione di admin(ovvero non possiede il ruolo admin)
# Avrei potuto utilizzare @admin_permission.require() al posto del decoratore personalizzato, tuttavia così non posso gestire l'errore
# Avrei anche potuto creare un try all'interno della funzione(come ho fatto nella funzione del decoratore), però ho preferito mantenere il codice pulito
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            admin_permission.test()
        except PermissionDenied:
            flash('Non hai il permesso di amministratore per accedere a questa pagina', 'error')
            return redirect(url_for('auth.home'))  
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            seller_permission.test()
        except PermissionDenied:
            flash('Non hai il permesso di venditore per accedere a questa pagina', 'error')
            return redirect(url_for('auth.home')) 
        return f(*args, **kwargs)
    return decorated_function

def buyer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs): 
        try:
            buyer_permission.test()
        except PermissionDenied:
            flash('Non hai il permesso di acquirente per accedere a questa pagina', 'error')
            return redirect(url_for('auth.home')) 
        return f(*args, **kwargs)
    return decorated_function