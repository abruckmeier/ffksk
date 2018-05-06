#!/usr/bin/env python
import os
import sys

import django

# Setup the Django environment of the Kiosk
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ffeKiosk.settings")
django.setup()


# Import the Modules
from django.conf import settings
from datetime import datetime

from kiosk.queries import readFromDatabase
from kiosk.bot import slack_SendMsg


# Elect best buyers and administrators
def electBestContributors():

    addressaten = []
    # Best Buyer
    data = readFromDatabase('getEinkaeuferDerWoche')
    addressaten.extend(x['slackName'] for x in data)
    if not data==[]:
        secBestBuyers = []
        for item in data[1:]:
            secBestBuyers.append(item['first_name'] + ' ' + item['last_name'])
        secBestBuyers = 'und '.join(secBestBuyers)

        bestBuyers = data[0]['first_name'] + ' ' + data[0]['last_name']
        if not secBestBuyers==[]:
            bestBuyers += ' (gefolgt von '+secBestBuyers+')'
    else:
        bestBuyers = None

    # Best Admininstrators
    data = readFromDatabase('getVerwalterDerWoche')
    addressaten.extend(x['slackName'] for x in data)
    if not data==[]:
        secBestAdmins = []
        for item in data[1:]:
            secBestAdmins.append(item['first_name'] + ' ' + item['last_name'])
        secBestAdmins = 'und '.join(secBestAdmins)

        bestAdmins = data[0]['first_name'] + ' ' + data[0]['last_name']
        if not secBestAdmins==[]:
            bestAdmins += ' (gefolgt von '+secBestAdmins+')'
    else:
        bestAdmins = None

    # Send the message
    if bestBuyers or bestAdmins:
        addressaten = ', '.join(['@'+x for x in list(set(addressaten))])
        msg = addressaten + chr(10)
        msg += '*Zeit für ein Lob:*'+chr(10)+chr(10)
        if bestBuyers:
            msg += ':trophy:\tGek'+chr(252)+'rt zum besten Eink'+chr(228)+'ufer dieser Woche wird '+bestBuyers+'!'+chr(10)
        if bestAdmins:
            msg += ':trophy:\tDer flei'+chr(223)+'igste Verwalter war diese Woche '+bestAdmins+'!'+chr(10)

        msg += chr(10)+'Vielen Dank f'+chr(252)+'r Deine Mithilfe im Kiosk!'

        slack_SendMsg(msg, channel=True)

    return


# Run the Script
if __name__ == '__main__':
    nowDate = datetime.utcnow()

    # Elect best buyers and administrators on Friday
    if nowDate.weekday()==4:
        print('It''s Friday. Elect best buyers and administrators.')
        try:
            electBestContributors()
        except:
            print('Error on posting the best buyers and administrators.')

    