HELPER_SETTINGS = {
    "INSTALLED_APPS": [
        "django_extensions",
        "djangocms_references",
        "djangocms_versioning",
        "djangocms_alias",
        "djangocms_references.test_utils.app_1",
        # "djangocms_references.test_utils.app_2",
    ],
    "MIGRATION_MODULES": {"djangocms_references": None},
}


def run():
    from djangocms_helper import runner

    runner.cms("djangocms_references", extra_args=[])


if __name__ == "__main__":
    run()
