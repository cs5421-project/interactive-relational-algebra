from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name='dispatch')
class LoadDatabaseView(View):

    def post(self, request: HttpRequest):
        # TODO
        return HttpResponse(request.body)
