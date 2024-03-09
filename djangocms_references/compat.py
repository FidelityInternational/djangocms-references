def is_versioning_installed():
    try:
        import djangocms_versioning  # noqa: F401
    except ImportError:
        return False
    else:
        return True


VERSIONING_INSTALLED = is_versioning_installed()
