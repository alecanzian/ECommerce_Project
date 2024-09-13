from flask import Flask
from flask_login import current_user
from flask_principal import  RoleNeed, UserNeed, identity_loaded
from blueprints.auth import app as auth_bp
from blueprints.profile import app as profile_bp
from blueprints.shop import app as shop_bp
from blueprints.account import app as account_bp

 
# Configurazione Flask
app = Flask(__name__, static_folder='../static', template_folder='../templates')
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(account_bp)

# The Identity represents the user, and is stored/loaded from various locations (eg session) for each request. The Identity is the user’s avatar to the system. It contains the access rights that the user has.
# A Need is the smallest grain of access control, and represents a specific parameter for the situation.Whilst a Need is a permission to access a resource, an Identity should provide a set of Needs that it has access to.
# A Permission is a set of requirements, any of which should be present for access to a resource.
@identity_loaded.connect
def on_identity_loaded(sender, identity):
    print("identity AGGIORNATA")
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