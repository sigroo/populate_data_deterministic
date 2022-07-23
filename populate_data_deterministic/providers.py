from datetime import timedelta

def update_user_password(instance, sp, ctx, meta=None):
    instance.set_password(sp["_password"])
    instance.save()
    return sp


def update_datetime_fields(ref_field, dt_fields):
    def update_datetime_fields_inner(fields, ctx, meta=None):
        dt = fields[ref_field]
        del fields[ref_field]
        for fld in dt_fields:
            if fld in fields and fields[fld] is not None:
                fld_type = meta["fields"][fld]["field"].__class__.__name__
                if fld_type == "DateField":
                    fields[fld] = (dt + timedelta(days=fields[fld])).strftime("%Y-%m-%d")
                else:
                    fields[fld] = dt + timedelta(days=fields[fld])
        return fields

    return update_datetime_fields_inner


def update_text_fields(ref, txt_fields):
    def update_text_fields_inner(fields, ctx, **kw):
        tref = fields[ref]
        del fields[ref]
        for fld in txt_fields:
            fields[fld] = tref + " " + fld
        return fields
    return update_text_fields_inner
