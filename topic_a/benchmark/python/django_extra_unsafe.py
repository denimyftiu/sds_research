def endpoint(User, value):
    return User.objects.extra(where=[f"name = '{value}'"])
