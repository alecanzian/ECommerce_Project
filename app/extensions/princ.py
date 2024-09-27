from flask import flash, redirect, url_for, current_app
from flask_login import current_user
from flask_principal import Principal, Permission, RoleNeed, PermissionDenied, UserNeed, identity_loaded, identity_changed, Identity
from functools import wraps

princ = Principal()

# Define role-based permissions
admin_permission = Permission(RoleNeed('admin'))
seller_permission = Permission(RoleNeed('seller'))
buyer_permission = Permission(RoleNeed('buyer'))

# The Identity represents the user, and is stored/loaded from various locations (eg session) for each request. The Identity is the user’s avatar to the system. It contains the access rights that the user has.
# A Need is the smallest grain of access control, and represents a specific parameter for the situation.Whilst a Need is a permission to access a resource, an Identity should provide a set of Needs that it has access to.
# A Permission is a set of requirements, any of which should be present for access to a resource.
@identity_loaded.connect
def on_identity_loaded(sender, identity):
    #print(sender)
    #print('carico identità')
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))
            #print(f'aggiunto ruolo {role.name}')
            
def update_identity(app, user_id):
    # Invia il segnale per aggiornare l'identità
    #print('invio segnale per aggiornare identita')
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

# Decoratore personalizzato per gestire il caso in cui l'utente non ha l'autorizzazione di admin(ovvero non possiede il ruolo admin) per accedere a info.html
# Avrei potuto utilizzare @admin_permission.require() al posto del decoratore personalizzato, tuttavia così non posso gestire l'errore
# Avrei anche potuto creare un try all'interno della funzione(come ho fatto nella funzione del decoratore), però ho preferito mantenere il codice pulito
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            admin_permission.test()
        except PermissionDenied:
            flash('You do not have admin permission to access this page.', 'error')
            return redirect(url_for('auth.home'))  
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            seller_permission.test()
        except PermissionDenied:
            flash('You do not have seller permission to access this page.', 'error')
            return redirect(url_for('auth.home')) 
        return f(*args, **kwargs)
    return decorated_function

def buyer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs): 
        try:
            buyer_permission.test()
        except PermissionDenied:
            flash('You do not have buyer permission to access this page.', 'error')
            return redirect(url_for('auth.home')) 
        return f(*args, **kwargs)
    return decorated_function