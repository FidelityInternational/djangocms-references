from django.db import models

from cms.models.pluginmodel import CMSPlugin

from ..polls.models import Poll


class NestedPoll(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)


class NestedPollPlugin(CMSPlugin):
    nested_poll = models.ForeignKey(NestedPoll, on_delete=models.CASCADE)


class DeeplyNestedPoll(models.Model):
    nested_poll = models.ForeignKey(NestedPoll, on_delete=models.CASCADE)


class DeeplyNestedPollPlugin(CMSPlugin):
    name = models.CharField(max_length=255)
    deeply_nested_poll = models.ForeignKey(DeeplyNestedPoll, on_delete=models.CASCADE)
