#!/usr/bin/env python

'''
    Create default users, necessary for running the kiosk
'''


import os
import sys
import django
from django.db import connection

if __name__ == '__main__':
    # Setup the Django environment of the Kiosk
    BASE = os.path.dirname(os.path.dirname(os.path.dirname((os.path.abspath(__file__)))))
    sys.path.append(BASE)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ffeKiosk.settings")
    django.setup()


# Import the Modules for the tasks
from django.conf import settings

from profil import models as profil_models
from kiosk import models as kiosk_models


def initNecessaryUsers():

    users = [
        ('Bank', 3),
        ('Bargeld', 2),
        ('PayPal_Bargeld', 24),
        ('Bargeld_Dieb', 73),
        ('Bargeld_im_Tresor', 72),
        ('Dieb', 4),
        ('Spendenkonto', 102),
    ]

    for u in users:

        _u, _created = profil_models.KioskUser.objects.update_or_create(
            id=u[1],
            username= u[0],
            defaults=dict(
                first_name= u[0],
                last_name= u[0],
                is_active= True,
                is_staff= False,
                is_superuser= False,
                slackName= u[0],
                is_verified = True,
                visible= False,
                aktivBis= '2999-12-31',
                rechte= 'User',
                is_functional_user=True,
            )
        )
        
        if _created:
            k = kiosk_models.Kontostand(
                nutzer= _u,
                stand= 0,
            )
            k.save()

    print('Necessary Users created.')

    # Reset the sql sequence
    with connection.cursor() as cursor:
        cursor.execute("""
                       SELECT setval(pg_get_serial_sequence('"profil_kioskuser_groups"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "profil_kioskuser_groups";
                       SELECT setval(pg_get_serial_sequence('"profil_kioskuser_user_permissions"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "profil_kioskuser_user_permissions";
                       SELECT setval(pg_get_serial_sequence('"profil_kioskuser"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "profil_kioskuser";
                       """)
    print('Resetted the database sequences due to explicit ids for the users')

    return


# Run the Script

if __name__ == '__main__':

    initNecessaryUsers()
    