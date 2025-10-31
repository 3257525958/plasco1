from django.conf import settings
from django.http import HttpResponseForbidden


class OfflineModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # فقط در حالت آفلاین IP چک شود
        if getattr(settings, 'OFFLINE_MODE', False):
            client_ip = self.get_client_ip(request)
            allowed_ips = getattr(settings, 'ALLOWED_OFFLINE_IPS', [])

            if client_ip not in allowed_ips:
                return HttpResponseForbidden(
                    "🚫 دسترسی غیرمجاز - این آدرس فقط برای IPهای داخلی شرکت قابل دسترسی است\n\n"
                    f"IP شما: {client_ip}\n"
                    f"IPهای مجاز: {', '.join(allowed_ips)}"
                )

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip