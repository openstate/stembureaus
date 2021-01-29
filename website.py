from app import app, db, cli

from app.models import (
    Gemeente, User, Gemeente_user, Election, BAG
)


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Gemeente': Gemeente,
        'User': User,
        'Gemeente_user': Gemeente_user,
        'Election': Election,
        'BAG': BAG
    }
