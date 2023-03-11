from django.urls import path

from . import views

urlpatterns = [
    path('execute_ra_query', views.execute_ra_query, name='execute_ra_query')
]
