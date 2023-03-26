import json
from http import HTTPStatus

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ira.model.output import Output
from ira.service.db_executor import execute_sql_query
from ira.service.lexer import Lexer
from ira.service.parser import Parser
from ira.service.transformer import transform


@method_decorator(csrf_exempt, name='dispatch')
class ExecuteRaQueryView(View):
    lexer = Lexer()
    parser = Parser()

    def post(self, request: HttpRequest):
        if request.body:
            request_body = json.loads(request.body)
            if self.is_request_valid(request_body):
                ra_query = request_body["raQuery"]
                try:
                    tokens = self.lexer.tokenize(ra_query)
                    parsed_postfix_tokens = self.parser.parse(tokens)
                    sql_query = transform(parsed_postfix_tokens)
                    output = execute_sql_query(sql_query)

                except Exception as exception:
                    output = Output(HTTPStatus.BAD_REQUEST,
                                    message="See exception message:{exception_message} for given raQuery:{ra_query}"
                                    .format(exception_message=exception, ra_query=ra_query),
                                    query=None)

                return JsonResponse(output.value, status=output.status_code)
        return JsonResponse({"message": "POST request not valid; Please ensure that only one attribute 'raQuery' is "
                                        "utilised."},
                            status=HTTPStatus.BAD_REQUEST)

    def is_request_valid(self, request_body: dict):
        return len(request_body.keys()) == 1 and "raQuery" in request_body
