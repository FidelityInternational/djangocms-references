from functools import lru_cache

from django.apps import apps


@lru_cache(maxsize=1)
def supported_models():
    try:
        app_config = apps.get_app_config("djangocms_references")
    except LookupError:
        return {}
    else:
        extension = app_config.cms_extension
        return extension.references_app_models
