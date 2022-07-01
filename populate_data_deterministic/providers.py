

def update_user_password(instance, sp, ctx):
    instance.set_password(sp["_password"])
    instance.save()
    return sp
