from cms import __version__ as cms_version

from packaging.version import Version


DJANGO_CMS_4_1 = Version(cms_version) >= Version('4.1')


def is_versioning_installed():
    try:
        import djangocms_versioning  # noqa: F401
    except ImportError:
        return False
    else:
        return True


VERSIONING_INSTALLED = is_versioning_installed()
