from django import forms

from .models import PollPlugin


class PollPluginForm(forms.ModelForm):
    class Meta:
        model = PollPlugin
        fields = ("template",)
