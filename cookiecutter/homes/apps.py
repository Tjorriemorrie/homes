from django.apps import AppConfig


class HomesConfig(AppConfig):
    name = 'homes'

    def ready(self):
        import homes.signals
