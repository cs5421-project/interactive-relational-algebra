from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from http import HTTPStatus
from django.views.decorators.csrf import csrf_exempt
from ira.service.raq_converter import *
import json


@method_decorator(csrf_exempt, name='dispatch')
class LoadXmlView(View):

    def post(self, request: HttpRequest):
        if not request.body:
            return JsonResponse({"message": "POST request is not valid. Ensure the body is not present"}, status=HTTPStatus.BAD_REQUEST)

        request_body = json.loads(request.body)
        if not self.is_request_valid(request_body):
            return JsonResponse({"message": "POST request is not valid. Ensure the body has only one attribute called content"}, status=HTTPStatus.BAD_REQUEST)

        xml = request_body["content"]

        try:
            raq = raq_converter(xml)
            return JsonResponse({"raq": raq}, status=HTTPStatus.OK)
        except Exception as e:
            return JsonResponse({"message": "invalid xml format"}, status=HTTPStatus.BAD_REQUEST)

    def is_request_valid(self, request_body: dict):
        return len(request_body.keys()) == 1 and "content" in request_body
