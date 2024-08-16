from http.server import BaseHTTPRequestHandler
import os
import sys
import django


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        BASE = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
        sys.path.append(BASE)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ffeKiosk.settings")
        django.setup()

        from profil.models import KioskUser
        from kiosk.bot import slack_SendMsg

        u = KioskUser.objects.get(username='abruckmeier')
        slack_SendMsg('Test!', u)

        from scripts.routines.dailyTasks import routine
        routine()

        self.send_response(200)
        self.end_headers()
