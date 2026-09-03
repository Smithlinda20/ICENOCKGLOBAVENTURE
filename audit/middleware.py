"""Lightweight middleware placeholder - kept so request-scoped audit hooks
(e.g. capturing IP address in future) can be added without touching
settings.py again. Currently a no-op pass-through."""


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
