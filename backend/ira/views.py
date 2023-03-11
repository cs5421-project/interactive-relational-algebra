from django.http import HttpResponse, HttpRequest, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json


# TODO: Later make this as a class based view
@require_POST
@csrf_exempt
def execute_ra_query(request: HttpRequest) -> object:
    if not request.body:
        request_body = json.loads(request.body)
        if is_execute_ra_query_request_valid(request_body):
            # TODO: Call core logic
            return HttpResponse(request.body)
    return HttpResponseBadRequest("Mandatory attributes databaseName and raQuery not found in request.")


def is_execute_ra_query_request_valid(request_body: dict):
    return "databaseName" in request_body and "raQuery" in request_body
