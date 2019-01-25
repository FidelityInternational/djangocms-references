from unittest.mock import patch

from django.test import TestCase

from djangocms_references.compat import is_versioning_installed


class VersioningInstalledTestCase(TestCase):
    def test_no_versioning(self):
        with patch.dict("sys.modules", {"djangocms_versioning": None}):
            self.assertFalse(is_versioning_installed())

    def test_versioning(self):
        with patch.dict("sys.modules", {"djangocms_versioning": "foo"}):
            self.assertTrue(is_versioning_installed())
