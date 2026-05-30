"""
WebGuard Pro — Jinja2 Environment (for PDF Reports)
"""

from jinja2 import Environment
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': reverse,
        'now': timezone.now,
    })
    return env
