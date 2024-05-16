=========
Changelog
=========

Unreleased
==========

1.5.0 (2024-05-16)
==================
* Python 3.10 support added
* Django 4.2 support added
* Dropped Python 3.7 and below version support
* Add reference link for djangocms-snippet app

1.4.3 (2024-02-07)
==========
* fix: URL of `show references` in action list of djangocms-versioning-filer list page
* fix: Added CMS_CONFIRM_VERSION4 in test_settings to show intent of using v4
* fix: fix circleci build errors

1.4.2 (2022-05-23)
==================
* fix: Preview link should close and open the link outside of the sideframe

1.4.1 (2022-05-13)
==================
* fix: All versions are shown for versionable content objects, only the latest versions for content objects should be shown.

1.4.0 (2022-04-28)
==================
* feat: djangocms-versioning-filer admin actions integration

1.3.2 (2022-04-26)
==================
* fix: Unpublish parameter updated to use state_selected

1.3.1 (2022-04-25)
==================
* fix: Filter state highlighted when selected

1.3.0 (2022-04-19)
==================
* feat: Added filter by latest state

1.2.0 (2022-04-14)
==================
* fix: Issue where a plugins name isn't the same as the registered plugin, treating a plugin as an object.
* feat: Handle references objects that can be deeply nested through model relationships.

1.1.1 (2022-04-11)
==================
* Fix: Added Alias list_action monkeypatch for references

1.1.0 (2022-04-06)
==================
* Feature: Added Alias configuration

1.0.1 (2022-03-31)
==================
* Fix: Added SVG manifest entry

1.0.0 (2022-03-30)
==================
* Added list action icon template and svg
* Python 3.8, 3.9 support added
* Django 3.0, 3.1 and 3.2 support added
* Python 3.5 and 3.6 support removed
* Django 1.11 support removed
