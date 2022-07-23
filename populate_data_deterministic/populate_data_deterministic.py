import inspect
import json
from collections import defaultdict
from functools import lru_cache
from typing import List, TypedDict, Type, Dict, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from django.apps import apps
    from django.db import models

GlobalRefMap = Dict[str, Dict[int, Union[int, None]]]


class RefMeta(TypedDict):
    name: str
    model: str
    field: models.Field
    setnull: bool


class CopyMeta(TypedDict):
    name: str
    field: models.Field


class ModelClassMeta(TypedDict):
    name: str
    copy_fields: List[CopyMeta]
    ref_fields: List[RefMeta]
    pk: CopyMeta
    fields: Dict[str, Union[CopyMeta, RefMeta]]


def create_ctx():
    return {
        "refs": defaultdict(dict)
    }


@lru_cache
def get_model_from_string(app_model_name):
    app_name, model_name = app_model_name.split('.')
    app = apps.get_app_config(app_name)
    model = app.get_model(model_name)
    return model


@lru_cache
def get_model_class_meta(model_class: Type[models.Model], EXCLUDED=[]) -> ModelClassMeta:
    name: str = model_class._meta.app_label + '.' + model_class.__name__
    copy_fields: List[CopyMeta] = []
    ref_fields: List[RefMeta] = []
    all_fields: Dict[str, Union[CopyMeta, RefMeta]] = {}
    res: ModelClassMeta = {"name": name, "copy_fields": copy_fields, "ref_fields": ref_fields, "fields": all_fields}
    for field in model_class._meta.fields:
        if getattr(field, "primary_key"):
            res["pk"] = {"name": field.name, "field": field}

        elif field.__class__.__name__ != "ForeignKey" and not getattr(
            field, "is_relation"
        ):
            spec = {"name": field.name, "field": field}
            copy_fields.append(spec)
            all_fields[field.name] = spec
        if getattr(field, "is_relation"):
            model_name = field.related_model.__name__
            fld_spec: RefMeta = {
                "name": field.name,
                "model": f"{field.related_model._meta.app_label}.{field.related_model.__name__}",
                "field": field,
                "setnull": False,
            }

            if model_name in EXCLUDED:
                fld_spec["setnull"] = True
            ref_fields.append(fld_spec)
            all_fields[field.name] = fld_spec
    return res


def create_spec(spec: dict, context: dict):
    """
    creates kwargs from spec which are good for model creation.
    """
    res = {}
    for attr in spec:
        if inspect.isfunction(spec[attr]):
            res[attr] = spec[attr](attr, res, context)
        else:
            res[attr] = spec[attr]
    return res


def dump_instance(model_class: Type[models.Model], source_instance: models.Model):
    meta = get_model_class_meta(model_class)
    instance_create_kwargs = {}
    for field_meta in meta["copy_fields"]:
        instance_create_kwargs[field_meta["name"]] = field_meta['field'].value_to_string(source_instance)
    for ref_field_meta in meta["ref_fields"]:
        if ref_field_meta["setnull"]:
            instance_create_kwargs[ref_field_meta["name"] + "_id"] = None
        else:
            instance_create_kwargs[ref_field_meta["name"] + "_id"] = ref_field_meta['field'].value_to_string(
                source_instance)
    print(json.dumps({
        "model": meta["name"],
        "pk": meta["pk"]["field"].value_to_string(source_instance),
        "fields": instance_create_kwargs}))


def get_objects(model_class: Type[models.Model]) -> models.QuerySet:
    """
    get all objects of a particular model if required based on some condition
    """
    return getattr(model_class, "objects")


def create_single_instance(model_class: Type[models.Model], source_fields: dict, ctx: dict, prev_pk=None,
                           param_processors=[], post_processors=[]):
    print("trying to create instance from ", source_fields)
    meta = get_model_class_meta(model_class)
    kwargs = {}
    references_map = ctx["refs"]
    processed_spec = create_spec(source_fields, ctx, meta=meta)
    source_fields = processed_spec
    process_params = len(param_processors) > 0
    post_process = len(post_processors) > 0
    if process_params:
        for processor in param_processors:
            source_fields = processor(source_fields, ctx, meta=meta)

    for field_name, field_meta in meta["fields"].items():
        field_attr_value, is_ref = None, False
        field = field_meta["field"]
        if field_name in source_fields:
            if "model" not in field_meta:  # copy field
                source_val = source_fields.get(field_name)
                if source_val == 'None' or source_val is None:
                    field_attr_value = None
                else:
                    field_attr_value = field.to_python(source_fields[field_name])
            else:
                if field_meta["setnull"] is True or field_meta["model"] not in references_map:
                    field_attr_value = None
                    is_ref = True
                else:
                    source_id = source_fields[field_name]
                    if source_id == 'None' or source_id is None:
                        current_source_id = None
                    else:
                        current_source_id = references_map[field_meta["model"]].get(source_id)
                    if current_source_id is not None:
                        field_attr_value = field.to_python(current_source_id)
                    else:
                        field_attr_value = None
                    is_ref = True

            kwargs[(field_name + '_id') if is_ref else field_name] = field_attr_value
    try:
        target_instance = get_objects(model_class).create(**kwargs)
    except Exception as e:
        print("unable to create instance for", source_fields, kwargs)
        print(str(e))
        return None
    else:
        print("created instance for", source_fields, kwargs)
    if post_process:
        for post_processor in post_processors:
            post_processor(target_instance, source_fields, ctx)

    references_map[meta["name"]][target_instance.pk] = target_instance.pk
    return target_instance


def create_instances_from_definition(model_class, spec, ctx, **kw):
    instances = []
    for single_spec in spec:
        instance = create_single_instance(model_class, single_spec, ctx, **kw)
        instances.append(instance)
    return instances


def create_instance_from_dump(spec, ctx, **kw):
    model = get_model_from_string(spec["model"])
    create_single_instance(model, spec["fields"], ctx["ref"], prev_pk=spec["pk"], **kw)
