from sqlalchemy import text
def endpoint(session, value):
    return session.execute(text("SELECT * FROM users WHERE name = :name"), {"name": value})
