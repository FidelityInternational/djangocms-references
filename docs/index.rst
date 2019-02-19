.. djangocms-references documentation master file, created by
   sphinx-quickstart on Thu Feb 14 11:45:02 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to djangocms-references's documentation!
================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Overview
--------

Django CMS References provides a way to retrieve objects
that are related to a selected object. It also includes a view
to present that data to the end user.

Relations used to retrieve these objects must be explicitly configured.

Glossary
--------

.. glossary::

    reference
        A reference is any relation to a certain object that has been
        defined in the configuration.

    referenced object
        An object that we want to show the :term:`references <reference>` of.

    referencing object
        An object that has a reference to a :term:`referenced object`.

Installation
------------

Run::

    pip install djangocms-references


Add ``djangocms_references`` to your project's ``INSTALLED_APPS``.

Include `djangocms_references.urls` in your URLs:

.. code-block:: python

    # project/urls.py
    urlpatterns += [
        url(r'', include('djangocms_references.urls'))
    ]

Configuration
-------------

References uses the Django CMS app registration system.
To configure your addon to use References, create a ``cms_config.py`` file
in your addon's folder. The most simple configuration looks like this:

.. code-block:: python

    # polls/models.py
    from django.db import models

    class Poll(models.Model):
        pass

    class Answer(models.Model):
        poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
        is_correct = models.BooleanField(default=False)

.. code-block:: python

    # polls/cms_config.py
    from cms.app_base import CMSAppConfig

    class PollsAppConfig(CMSAppConfig):
        djangocms_references_enabled = True
        reference_fields = [
            (Answer, 'poll'),
        ]

In this example, ``Answer`` can contain a reference to the ``Poll`` object.

:py:class:`CMSAppConfig`

    :py:attr:`~djangocms_references_enabled`

    Your ``cms_config.py`` needs to define a single subclass of ``CMSAppConfig``
    with ``djangocms_references_enabled = True``. This instructs Django CMS
    to pass your config to References extension.

    :py:attr:`~reference_fields`

    This attribute allows for registering places where the referenced objects are used.

    It needs to be a list of ``(model, field)`` tuples.

    .. important::
       References addon requires explicit definition of places where references
       can happen.

    :py:attr:`~reference_list_extra_columns`

    A list of ``(func, column_name)`` tuples, where ``func`` is a function
    that accepts a :term:`referencing object` parameter.

    Every element defines a new column that is added to reference list.
    It can be used to extend the functionality of reference list view.

    Example:

    .. code-block:: python

        def is_even_pk(obj):
            return obj.pk % 2 == 0

        class PollsAppConfig(CMSAppConfig):
            ...
            reference_list_extra_columns = [
                (is_even_pk, 'Is even?'),
            ]

    :py:attr:`~reference_list_queryset_modifiers`

    A list of functions, which accept ``queryset`` argument and are supposed to return a modified queryset.
    They are applied to all querysets of objects referencing a given object.

    Example:

    .. code-block:: python

        def show_only_correct_answers(queryset):
            if queryset.model == Answer:
                return queryset.filter(is_correct=True)
            return queryset

        class PollsAppConfig(CMSAppConfig):
            ...
            reference_list_queryset_modifiers = [show_only_correct_answers]

    .. note::
        :py:attr:`~reference_list_queryset_modifiers` and
        :py:attr:`~reference_list_extra_columns` are usually used together.
        Queryset modifier adds new fields using ``.annotate()`` and extra column displays that data.

Usage
-----

After configuring the relations, a "Show references" button will appear
in the CMS toolbar.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
