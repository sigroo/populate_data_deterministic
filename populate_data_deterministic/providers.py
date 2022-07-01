

def update_user_password(instance, sp, ctx):
    instance.set_password(sp["password"])
    instance.save()
    return sp
