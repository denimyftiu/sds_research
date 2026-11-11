def endpoint(User, value):
    return User.objects.raw(f"SELECT * FROM users WHERE name = '{value}'")
