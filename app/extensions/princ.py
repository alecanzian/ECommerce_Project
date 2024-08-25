from flask import flash, redirect, url_for
from flask_login import current_user
from flask_principal import Principal, Permission, PermissionDenied, RoleNeed
from functools import wraps

princ = Principal()

# Define role-based permissions
admin_permission = Permission(RoleNeed('admin'))
seller_permission = Permission(RoleNeed('seller'))
buyer_permission = Permission(RoleNeed('buyer'))
            
# Decoratore personalizzato per gestire il caso in cui l'utente non ha l'autorizzazione(ovvero non possiede il ruolo) per eseguire una azione
def anonymous_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            flash('Devi prima eseguire il log out', category = 'error')
            return redirect(url_for('auth.logout'))  # Redirige alla home se l'utente è loggato
        return f(*args, **kwargs)
    return decorated_function

# Decoratore personalizzato per gestire il caso in cui l'utente non ha l'autorizzazione di admin(ovvero non possiede il ruolo admin) per accedere a info.html
# Avrei potuto utilizzare @admin_permission.require() al posto del decoratore personalizzato, tuttavia così non posso gestire l'errore
# Avrei anche potuto creare un try all'interno della funzione(come ho fatto nella funzione del decoratore), però ho preferito mantenere il codice pulito
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #try:
        #    admin_permission.test()
        #except PermissionDenied:
        if not current_user.has_role('admin'):
            flash('You do not have admin permission to access this page.', 'error')
            # Reindirizza alla pagina dello shop se l'utente non è admin
            return redirect(url_for('shop.shop'))  
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #try:
        #    seller_permission.test()
        #except PermissionDenied:
        if not current_user.has_role('seller'):
            flash('You do not have seller permission to access this page.', 'error')
            # Reindirizza alla pagina dello shop se l'utente non è admin
            return redirect(url_for('auth.logout'))  
        return f(*args, **kwargs)
    return decorated_function

def buyer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs): 
        #try:
        #    buyer_permission.test()
        #except PermissionDenied:
        if not current_user.has_role('buyer'):
            flash('You do not have buyer permission to access this page.', 'error')
            # Reindirizza alla pagina dello shop se l'utente non è admin
            return redirect(url_for('auth.logout'))  
        return f(*args, **kwargs)
    return decorated_function