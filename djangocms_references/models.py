from django.db import models
from django.utils.translation import gettext_lazy as _


class References(models.Model):
    """Dummy model used for permission handling. No DB tables are
    actually created.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (("show_references", _("Can show references")),)
