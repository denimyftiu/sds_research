from sqlalchemy import text
def endpoint(session, value):
    return session.execute(text(f"SELECT * FROM users WHERE name = '{value}'"))
