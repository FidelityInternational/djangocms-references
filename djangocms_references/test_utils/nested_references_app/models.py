from django.db import models

from cms.models.pluginmodel import CMSPlugin

from ..polls.models import Poll


class ThroughModel(models.Model):
    grouper = models.ForeignKey(Poll, on_delete=models.CASCADE)


class NestedPoll(models.Model):
    through = models.ForeignKey(ThroughModel, on_delete=models.CASCADE)


class NestedPollPlugin(CMSPlugin):
    name = models.CharField(max_length=255)
    nested_poll = models.ForeignKey(NestedPoll, on_delete=models.CASCADE)


class DeeplyNestedPollPlugin(CMSPlugin):
    name = models.CharField(max_length=255)
    nested_poll = models.ForeignKey(NestedPoll, on_delete=models.CASCADE)
