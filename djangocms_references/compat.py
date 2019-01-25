from distutils.version import LooseVersion

import django


DJANGO_GTE_21 = LooseVersion(django.get_version()) >= LooseVersion("2.1")


def is_versioning_installed():
    try:
        import djangocms_versioning  # noqa: F401
    except ImportError:
        return False
    else:
        return True


VERSIONING_INSTALLED = is_versioning_installed()
