# Synthetic workflow fixture; never a real-project observation.
from sqlalchemy import text

def find(cursor, session, User, value):
    cursor.execute("SELECT * FROM users WHERE name = '" + value + "'")
    session.execute(text("SELECT * FROM users WHERE name = :name"), {"name": value})
    return User.objects.filter(name=value)
