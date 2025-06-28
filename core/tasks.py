from __future__ import absolute_import, unicode_literals

from celery import shared_task

import logging
logger = logging.getLogger(__name__)

import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

@shared_task
def test_task():
    """
    An example Celery task that logs a message.
    """
    logger.info("This is an example task running in the background.")
    return "Task completed successfully!"