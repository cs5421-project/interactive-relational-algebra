import json

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt


def is_execute_ra_query_request_valid(request_body: dict):
    return "databaseName" in request_body and "raQuery" in request_body


@method_decorator(csrf_exempt, name='dispatch')
class ExecuteRaQueryView(View):

    def post(self, request: HttpRequest):
        if not request.body:
            request_body = json.loads(request.body)
            if is_execute_ra_query_request_valid(request_body):
                # TODO: Call core logic
                return HttpResponse(request.body)
        return HttpResponseBadRequest("Mandatory attributes databaseName and raQuery not found in request.")
