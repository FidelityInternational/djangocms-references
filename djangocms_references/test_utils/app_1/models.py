from django.db import models


class Parent(models.Model):
    pass


class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
