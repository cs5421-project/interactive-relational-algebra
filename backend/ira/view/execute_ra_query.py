import json
from http import HTTPStatus

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ira.service.db_executor import execute_sql_query
from ira.service.transformer import transform


@method_decorator(csrf_exempt, name='dispatch')
class ExecuteRaQueryView(View):

    def post(self, request: HttpRequest):
        if request.body:
            request_body = json.loads(request.body)
            if self.is_request_valid(request_body):
                # TODO: Call core logic
                # TODO: Remove stub argument
                query = transform(["sample"])
                output = execute_sql_query(query)
                return JsonResponse(output.value, status=output.status_code)
        return JsonResponse({"message": "Request not valid; Please ensure that only one attribute 'raQuery' is "
                                        "utilised."},
                            status=HTTPStatus.BAD_REQUEST)

    def is_request_valid(self, request_body: dict):
        return len(request_body.keys()) == 1 and "raQuery" in request_body
