from aldryn_client import forms


class Form(forms.BaseForm):
    def to_settings(self, data, settings):
        settings['ADDON_URLS'].append('djangocms_references.urls')
        return settings
