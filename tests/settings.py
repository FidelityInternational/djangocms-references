HELPER_SETTINGS = {
    "SECRET_KEY": "djangocmsreferencestestsuitekey",
    "INSTALLED_APPS": [
        "djangocms_alias.apps.AliasConfig",
        "djangocms_references",
        "djangocms_versioning",
        "djangocms_references.test_utils.app_1",
        "djangocms_references.test_utils.polls",
    ],
    "MIGRATION_MODULES": {
        "auth": None,
        "cms": None,
        "menus": None,
        "djangocms_references": None,
        "djangocms_versioning": None,
        "djangocms_alias": None,
        "djangocms_references.test_utils.polls": None,
    },
    "DEFAULT_AUTO_FIELD": "django.db.models.AutoField",
    "ROOT_URLCONF": "tests.urls",
}


def run():
    from app_helper import runner

    runner.cms("djangocms_references", extra_args=[])


if __name__ == "__main__":
    run()
