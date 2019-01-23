from django.template import Context, Template
from django.template.exceptions import TemplateSyntaxError
from django.test import TestCase

from cms.toolbar.utils import get_object_preview_url

from .factories import PageContentFactory


class ReferencesTemplateTagTest(TestCase):
    def test_object_preview_url_rendered_with_obj_arg(self):
        obj = PageContentFactory()
        context = Context({"obj": obj})
        expected_url = get_object_preview_url(obj)
        template_to_render = Template(
            "{% load djangocms_references_tags %}" "{% object_preview_url obj %}"
        )
        rendered_template = template_to_render.render(context)
        self.assertInHTML(expected_url, rendered_template)

    def test_object_preview_url_rendered_with_string_arg(self):
        obj = PageContentFactory()
        context = Context({"obj": obj})
        template_to_render = Template(
            "{% load djangocms_references_tags %}" "{% object_preview_url 'dummy' %}"
        )
        self.assertRaises(TemplateSyntaxError, template_to_render.render, context)

    def test_object_preview_url_rendered_with_int_arg(self):
        obj = PageContentFactory()
        context = Context({"obj": obj})
        template_to_render = Template(
            "{% load djangocms_references_tags %}" "{% object_preview_url 123 %}"
        )
        self.assertRaises(TemplateSyntaxError, template_to_render.render, context)

    def test_object_model_rendered_with_obj_arg(self):
        obj = PageContentFactory()
        context = Context({"obj": obj})
        expected_model = obj._meta.model_name
        template_to_render = Template(
            "{% load djangocms_references_tags %}" "{% object_model obj %}"
        )
        rendered_template = template_to_render.render(context)
        self.assertEqual(expected_model, rendered_template)

    def test_object_model_rendered_with_string_argument(self):
        obj = PageContentFactory()
        context = Context({"obj": obj})
        template_to_render = Template(
            "{% load djangocms_references_tags %}" '{% object_model "dummy" %}'
        )
        self.assertRaises(TemplateSyntaxError, template_to_render.render, context)

    def test_object_model_rendered_with_int_argument(self):
        obj = PageContentFactory()
        context = Context({"obj": obj})
        template_to_render = Template(
            "{% load djangocms_references_tags %}" "{% object_model 1 %}"
        )
        self.assertRaises(TemplateSyntaxError, template_to_render.render, context)
