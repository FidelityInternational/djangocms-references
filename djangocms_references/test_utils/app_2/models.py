from django.db import models


class GrouperModel(models.Model):
    name = models.CharField(max_length=255)


class ContentModelBase(models.Model):
    grouper = models.ForeignKey(GrouperModel, on_delete=models.PROTECT)

    class Meta:
        abstract = True


class ContentModel(ContentModelBase):
    label = models.CharField(max_length=255)


class ExtensionModel(ContentModelBase):
    def __str__(self):
        return self.grouper.name
