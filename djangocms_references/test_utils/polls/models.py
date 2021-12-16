from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin


class Poll(models.Model):
    name = models.TextField()


class PollContent(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    language = models.TextField()
    text = models.TextField()


TEMPLATE_DEFAULT = "0"


def get_templates():
    choices = [("0", _("Default")), ("1", _("Choice 1")), ("2", _("Choice 2"))]

    return choices


class PollPlugin(CMSPlugin):
    poll = models.ForeignKey(
        Poll,
        verbose_name=_("polls"),
        related_name="cms_plugins",
        on_delete=models.CASCADE,
    )
    template = models.CharField(
        verbose_name=_("template"),
        choices=get_templates(),
        default=TEMPLATE_DEFAULT,
        max_length=255,
        null=True,
        blank=True,
    )
