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
from shutil import copyfile
from slackclient import SlackClient

from kiosk.queries import readFromDatabase
from kiosk.bot import slack_SendMsg
from profil.models import KioskUser


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
        if not secBestBuyers=='':
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
        if not secBestAdmins=='':
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


# Conduct the daily rotating Save of the Database
def dailyBackup(nowDate):

    # Get information and stop if not activated
    backupSettings = getattr(settings,'BACKUP')
    if not backupSettings['active']:
        print('Backup not activated in settings. Stop.')
        return 'Backup not activated in settings.'

    # Get the origin of the to copy file
    baseDir = getattr(settings,'BASE_DIR')
    databaseName = getattr(settings,'DATABASE_NAME')
    
    # Get the backup folder and create the day-specific file name of the backup file
    backupFolder = backupSettings['backupFolder']
    if not os.path.exists(backupFolder):
        print('Backup Folder does not exist. Create it...')
        os.makedirs(backupFolder)

    destinationDbName = 'save_'+str(nowDate.weekday())+'_'+databaseName

    # Copy the file to the destination
    copyfile(os.path.join(baseDir,databaseName), os.path.join(backupFolder,destinationDbName))

    return str(os.path.join(backupFolder,destinationDbName))


def weeklyBackup(nowDate):

    # Get information and stop if not activated
    backupSettings = getattr(settings,'BACKUP')
    if not backupSettings['active']:
        print('Backup not activated in settings. Stop.')
        return 'Backup not activated in settings.'

    # Get the origin of the to attach file
    baseDir = getattr(settings,'BASE_DIR')
    databaseName = getattr(settings,'DATABASE_NAME')
    
    # Get the backup folder
    backupFolder = backupSettings['backupFolder']
    if not os.path.exists(backupFolder):
        print('Backup Folder does not exist. Create it...')
        os.makedirs(backupFolder)

    # Create the day-specific file name of the backup file
    attDatabaseName = 'save_'+datetime.strftime(nowDate,'%Y-%m-%dT%H-%M-%S-%fZ')+'_'+databaseName

    # Copy the file to the destination
    copyfile(os.path.join(baseDir,databaseName), os.path.join(backupFolder,attDatabaseName))

    # Send the database attached as Slack-message
    slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
    sc = SlackClient(slack_token)

    for usr in backupSettings['sendWeeklyBackupToUsers']:
        sc.api_call(
            'files.upload', 
            channels='@'+usr, 
            as_user=True,
            text='test',
            filename=attDatabaseName, 
            file=open(os.path.join(baseDir,databaseName), 'rb'),
        )

        # Send additional message to the receivers of the attached database
        slack_SendMsg('You received the database attached as backup in an other message. Please save the file to a secure place and delete the Slack message!', userName=usr)

    return {
        'weeklyStoredAtServer':str(os.path.join(backupFolder,attDatabaseName)), 
        'weeklySentToUsers': ['@'+x for x in backupSettings['sendWeeklyBackupToUsers']],
    }



# Run the Script
if __name__ == '__main__':
    
    nowDate = datetime.utcnow()

    # Elect best buyers and administrators on Friday
    if nowDate.weekday()==4:
        print('It''s Friday. Elect best buyers and administrators.')
        try:
            electBestContributors()
            print('Done electing best buyers and administrators.')
        except:
            print('Error on posting the best buyers and administrators.')

    
    # Conduct the daily rotating Save of the Database
    print('Do the daily backup of the database.')
    try:
        dest = dailyBackup(nowDate)
        msg = 'Daily Backup of the Database File successfully stored under `'+dest+'`.'

        # Send message to all admins
        data = KioskUser.objects.filter(visible=True, rechte='Admin')
        for u in data:
            slack_SendMsg(msg, user=u)

        print('Finished the daily backup.')

    except:
        # Send failure message to all admins
        data = KioskUser.objects.filter(visible=True, rechte='Admin')
        try:
            for u in data:
                slack_SendMsg('The daily backup of the Database failed!', user=u)
            print('Daily Backup failed. Slack Message sent.')
        except:
            print('Failing to send Slack Message with Fail Notice of database daily backup.')


    # Conduct a weekly Backup of the database: Send via Slack to the Admins
    if nowDate.weekday()==3:
        print('It''s Thursday. Do the weekly backup.')
        try:
            ret = weeklyBackup(nowDate)
            msg = 'Weekly Backup of the Database File successfully stored under `'+ret['weeklyStoredAtServer']+'` and sent to '+', '.join(ret['weeklySentToUsers'])+' .'

            # Send message to all admins
            data = KioskUser.objects.filter(visible=True, rechte='Admin')
            for u in data:
                slack_SendMsg(msg, user=u)

            print('Finished the weekly backup.')

        except:
            # Send failure message to all admins
            data = KioskUser.objects.filter(visible=True, rechte='Admin')
            try:
                for u in data:
                    slack_SendMsg('The weekly backup of the Database failed!', user=u)
                print('Weekly Backup failed. Slack Message sent.')
            except:
                print('Failing to send Slack Message with Fail Notice of database weekly backup.')
