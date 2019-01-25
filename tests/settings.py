HELPER_SETTINGS = {
    "INSTALLED_APPS": [
        "djangocms_references",
        "djangocms_versioning",
        "djangocms_references.test_utils.app_1",
        "djangocms_references.test_utils.polls",
        # "djangocms_references.test_utils.app_2",
    ],
    "MIGRATION_MODULES": {
        "auth": None,
        "cms": None,
        "menus": None,
        "djangocms_references": None,
        "djangocms_versioning": None,
        "djangocms_references.test_utils.polls": None,
    },
}


def run():
    from djangocms_helper import runner

    runner.cms("djangocms_references", extra_args=[])


if __name__ == "__main__":
    run()
