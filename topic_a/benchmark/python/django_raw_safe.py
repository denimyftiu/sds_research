def endpoint(User, value):
    return User.objects.raw("SELECT * FROM users WHERE name = %s", [value])
