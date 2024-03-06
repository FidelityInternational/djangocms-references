from cms import __version__ as cms_version


try:
    from packaging.version import Version
except ModuleNotFoundError:
    from distutils.version import LooseVersion as Version


def is_versioning_installed():
    try:
        import djangocms_versioning  # noqa: F401
    except ImportError:
        return False
    else:
        return True


DJANGO_CMS_4_1 = Version(cms_version) >= Version('4.1')


VERSIONING_INSTALLED = is_versioning_installed()
