from .models import SystemSettings


def store_settings(request):
    return {"store_settings": SystemSettings.load()}
