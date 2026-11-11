def endpoint(cursor, value):
    cursor.execute("SELECT * FROM users WHERE name = ?", (value,))
