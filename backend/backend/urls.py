from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('v1/ira/', include('ira.urls')),
    path('admin/', admin.site.urls),
]


def init():
    create_predefined_databases()


def create_predefined_databases():
    # TODO
    pass
