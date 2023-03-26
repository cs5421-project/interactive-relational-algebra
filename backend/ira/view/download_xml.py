import json
from http import HTTPStatus

from django.http import HttpRequest, HttpResponse, JsonResponse, FileResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ira.model.output import Output
from ira.service.lexer import Lexer
from ira.service.xml_convertor import convert_tokenized_ra_to_xml


@method_decorator(csrf_exempt, name='dispatch')
class DownloadXmlView(View):
    lexer = Lexer()

    def post(self, request: HttpRequest):
        if request.body:
            request_body = json.loads(request.body)
            if self.is_request_valid(request_body):
                ra_query = request_body["raQuery"]
                try:
                    tokens = self.lexer.tokenize(ra_query)
                    xml_content = convert_tokenized_ra_to_xml(tokens).get_tree()
                    return FileResponse(xml_content,content_type="applications/xml",
                                        as_attachment=True)
                except Exception as exception:
                    output = Output(HTTPStatus.BAD_REQUEST,
                                    message="See exception message:{exception_message} for given raQuery:{ra_query}"
                                    .format(exception_message=exception, ra_query=ra_query),
                                    query=None)
                return JsonResponse(output.value,status=HTTPStatus.BAD_REQUEST)
        return JsonResponse({"message": "POST request not valid; Please ensure that only one attribute 'raQuery' is "
                                        "utilised."},
                            status=HTTPStatus.BAD_REQUEST)

    def is_request_valid(self, request_body: dict):
        return len(request_body.keys()) == 1 and "raQuery" in request_body
