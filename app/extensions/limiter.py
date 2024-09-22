from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    get_remote_address,  # Utilizza l'indirizzo IP dell'utente come chiave per il rate limit
    default_limits=["500 per day", "100 per hour"]  # Limiti per le richieste
)