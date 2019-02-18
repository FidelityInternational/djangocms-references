from django.db import models


class Parent(models.Model):

    def __str__(self):
        return str(self.pk)


class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)


class UnknownChild(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
