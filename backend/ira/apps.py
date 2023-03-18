from django.apps import AppConfig

from ira.service.pre_populator import pre_populate


class IraConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ira'

    def ready(self):
        pre_populate()




