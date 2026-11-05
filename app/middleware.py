from .ui_i18n import clear_current_language, get_language_from_request, set_current_language


class UiLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = get_language_from_request(request)
        request.ui_language = language
        set_current_language(language)
        try:
            response = self.get_response(request)
        finally:
            clear_current_language()
        return response
