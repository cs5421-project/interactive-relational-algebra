from django.test import TestCase
from django.test import Client
from django.urls import reverse
from http import HTTPStatus


# TODO: Make this under test package and make sure manage.py test does not break
class ExecuteRaViewTests(TestCase):

    def test_is_request_valid(self):
        client = Client()
        response = client.post(reverse("execute_ra_query"), data={})
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

