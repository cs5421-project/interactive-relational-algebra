from django.urls import path

from .view.download_xml import DownloadXmlView
from .view.execute_ra_query import ExecuteRaQueryView
from .view.load_xml import LoadXmlView

urlpatterns = [
    path('execute_ra_query', ExecuteRaQueryView.as_view(), name='execute_ra_query'),
    path('download_xml', DownloadXmlView.as_view(), name='download_xml'),
    path('load_xml', LoadXmlView.as_view(), name='load_xml')
]
