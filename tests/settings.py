HELPER_SETTINGS = {
    "INSTALLED_APPS": ["djangocms_references"],
    "MIGRATION_MODULES": {"djangocms_references": None},
}


def run():
    from djangocms_helper import runner

    runner.cms("djangocms_references", extra_args=[])


if __name__ == "__main__":
    run()
