def endpoint(User, value):
    return User.objects.extra(where=["name = %s"], params=[value])
