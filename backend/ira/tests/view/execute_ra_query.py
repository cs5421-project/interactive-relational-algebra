from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


class ExecuteRaViewTests(TestCase):
    # FIXME: Getting exception:
    #  DJANGO_SETTINGS_MODULE or call settings.configure() before accessing settings
    pass
    # def test_is_request_valid(self):
    #     client = Client()
    #     response = client.post(reverse("execute_ra_query"), data={})
    #     self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
