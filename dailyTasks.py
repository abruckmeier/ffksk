#!/usr/bin/env python
import os
import sys

import django

# Setup the Django environment of the Kiosk
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ffeKiosk.settings")
django.setup()


# Import the Modules
from django.conf import settings
from datetime import datetime, timedelta
import pytz
from shutil import copyfile
from slackclient import SlackClient
import time

from kiosk.queries import readFromDatabase
from kiosk.bot import slack_SendMsg, checkKioskContentAndFillUp
from profil.models import KioskUser
from kiosk.models import ZumEinkaufVorgemerkt


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
        secBestBuyers = ' und '.join(secBestBuyers)

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
        secBestAdmins = ' und '.join(secBestAdmins)

        bestAdmins = data[0]['first_name'] + ' ' + data[0]['last_name']
        if not secBestAdmins=='':
            bestAdmins += ' (gefolgt von '+secBestAdmins+')'
    else:
        bestAdmins = None

    # Send the message
    if bestBuyers or bestAdmins:
        addressaten = ', '.join(['@'+x for x in list(set(addressaten))])
        msg = addressaten + chr(10)
        msg += '*Zeit f'+chr(252)+'r ein Lob:*'+chr(10)+chr(10)
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
        slack_SendMsg('You received the database attached as backup in an other message to the kioskbot. Do not save the file otherwise! This file will be deleted in one year from the thread.', userName=usr)

    return {
        'weeklyStoredAtServer':str(os.path.join(backupFolder,attDatabaseName)), 
        'weeklySentToUsers': ['@'+x for x in backupSettings['sendWeeklyBackupToUsers']],
    }


# 
def deleteOldWeeklyBackupsFromSlackAdmin(nowDate):

    # Unix Epoche of timestamp half a year before
    dt = (nowDate - timedelta(days=182) - datetime(1970,1,1,tzinfo=pytz.utc)).total_seconds()

    # Get information and stop if not activated
    backupSettings = getattr(settings,'BACKUP')
    if not backupSettings['active']:
        print('Backup not activated in settings. Stop.')
        return 'Backup not activated in settings.'

    slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
    sc = SlackClient(slack_token)

    for botID in backupSettings['kioskbotChannel']:
        conversation = sc.api_call(
            'conversations.history', 
            channel=botID,
        )
        
        if not conversation.get('ok', False):
            print('deleteOldWeeklyBackupsFromSlackAdmin: For botID {}, no messages found.'.format(botID))

        to_delete_msgs = [ msg.get('ts','') for msg in conversation.get('messages',[]) if float(msg.get('ts')) < dt  ]

        print('Deletion of following {} messages:'.format(str(len(to_delete_msgs))))
        for ts in to_delete_msgs:
            ret = sc.api_call(
                'chat.delete',
                channel=botID,
                ts = ts,
            )
            print(ret)
            time.sleep(2)


# Delete products in personal shopping list older than 7 days
def deleteTooOldProductsInShoppingList(nowDate):

    # Get items older than seven days
    t = nowDate - timedelta(days=7)
    oldItems = ZumEinkaufVorgemerkt.objects.filter(einkaufsvermerkUm__lt=t)
    
    # Notification of deletion to users
    userIDs = [o.einkaeufer_id for o in oldItems]
    userIDs = list(set(userIDs))
    for userID in userIDs:
        u = KioskUser.objects.get(id=userID)
        msg = 'Produkte, die l'+chr(228)+'nger als sieben Tage in deiner pers'+chr(246)+'nlichen Einkaufsliste waren, wurden nun wieder in die offene Einkaufsliste zur'+chr(252)+'ckgeschrieben. Du hast nun nicht mehr das Vorrecht, diese Produkte zu kaufen. \nUnter https://ffekiosk.pythonanywhere.com/menu/meineeinkaufe/ kannst du deine ver'+chr(228)+'nderte pers'+chr(246)+'nliche Einkaufsliste einsehen. Unter https://ffekiosk.pythonanywhere.com/menu/einkaufsvormerkungen/ kannst du neue Produkte in deine pers'+chr(246)+'nliche Einkaufsliste aufnehmen.\nDein Kiosk-Team'
        slack_SendMsg(msg,u)

    # Delete the items and refill the Kiosk
    oldItems.delete()
    checkKioskContentAndFillUp()

    return


# Give a warning message to buyers with products in personal shopping list older than 4 days
def warningTooOldProductsInShoppingList():

    # Get old Products and the users
    items = readFromDatabase('getZumEinkaufVorgemerktOlderThan4Days')

    # Get the relevant users for sending messages
    userSlackNames = [x['slackName'] for x in items]
    userSlackNames = list(set(userSlackNames))

    # For each user
    for u in userSlackNames:
        # Get his items older than 4 days
        uItems = [x for x in items if x['slackName']==u]

        #
        msg = '*Vorsicht!*\nDu hast vor vier (oder mehr) Tagen folgende Produkte in deine pers'+chr(246)+'nliche Einkaufsliste aufgenommen und noch nicht eingekauft:\n\n'
        for i in uItems:
            msg += '\t' + str(i['anzahl']) + 'x ' + i['produktName'] + '\n'
        msg += '\n Du hast insgesamt sieben Tage Zeit, deine Besorgungen f'+chr(252)+'r den Kiosk zu machen. Wurde nach dieser Zeit kein Einkauf bei einem Verwalter abgegeben, werden die entsprechenden Produkte aus deiner pers'+chr(246)+'nlichen Einkaufsliste gel'+chr(246)+'scht und wandern wieder in die offene Einkaufsliste.'+'\nUnter https://ffekiosk.pythonanywhere.com/menu/meineeinkaufe/ kannst du deine pers'+chr(246)+'nliche Einkaufsliste einsehen und modifizieren.\nDein Kiosk-Team'

        slack_SendMsg(msg, userName=u)

    return


# Warn Users who are going to be blocked soon
def warnUsersToBeBlockedSoon():

    # Get the users who are going to be blocked and are not yet warned
    users = readFromDatabase('getUsersToBeBlockedSoon')

    msg = 'Liebe*r Kiosknuzter*in,\nDu hast in Deinen Einstellungen (https://ffekiosk.pythonanywhere.com/accounts/angestellt_bis_change/) vermerkt, dass Dein Besch'+chr(228)+'ftigungsverh'+chr(228)+'ltnis zum {{date_end}} endet. Deshalb senden wir Dir diese Nachricht.\nNach diesem Datum wird Dein Benutzeraccount inaktiv gesetzt und Du kannst nicht mehr am FfE-Kiosk teilnehmen. Denke bitte daran, Dein Guthaben bei einem Verwalter ausbezahlen zu lassen. Danke, dass Du den FfE-Kiosk genutzt hast!\nFalls Du l'+chr(228)+'nger an der FfE bleibst, kannst Du das Datum Deines Austritts aus der FfE in Deinen Einstellungen einfach korrigieren.\nDein Kiosk-Team '

    for u in users:
        user = KioskUser.objects.get(id=u['id'])

        # Send the message to the user
        msgSend = msg.replace('{{date_end}}',datetime.strftime(u['aktivBis'],'%d.%m.%Y'))
        slack_SendMsg(msgSend, user=user)

        # Set the flag that user has been warned
        user.activity_end_msg = 1
        user.save()

    return


# Block user after active time
def blockUserAfterActiveTime(nowDate):
    t = nowDate + timedelta(days=1)
    users = KioskUser.objects.filter(aktivBis__lt=t, visible=True, is_active=True, activity_end_msg=1)

    msg = 'Liebe*r Kiosknuzter*in,\nHeute endet dein Besch'+chr(228)+'ftiungsverh'+chr(228)+'ltnis an der FfE und somit auch deine Aktivit'+chr(228)+'t im FfE-Kiosk. Dein Account ist nun inaktiv gesetzt, du kannst also keine Eink'+chr(228)+'ufe mehr t'+chr(228)+'tigen.\nHattest du noch Guthaben auf deinem Konto? Dann lasse dir dies von einem Verwalter ausbezahlen.\n Du verl'+chr(228)+'sst die FfE noch gar nicht? Dann reaktiviere dein Konto unter https://ffekiosk.pythonanywhere.com/accounts/angestellt_bis_change/.\nIn einem Monat werden deine personenbezogenen Daten gel'+chr(246)+'scht, danach ist eine Reaktivierung nicht mehr m'+chr(246)+'glich.\n\nDanke, dass du den FfE-Kiosk genutzt hast!\nDein Kiosk-Team'

    for u in users:

        msgSend = msg
        slack_SendMsg(msgSend, user=u)

        # Set status, that message has been sent
        u.activity_end_msg = 2

        # Make user inactive and invisible
        u.visible = False
        u.is_active = False

        u.save()
    return

# Run the Script
if __name__ == '__main__':
    
    nowDate = datetime.utcnow()
    nowDate = pytz.utc.localize(nowDate)
    
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
    # Furthermore, delete old weekly backups from the conversation
    if nowDate.weekday()==3:
        print('It''s Thursday. Do the weekly backup.')
        try:
            deleteOldWeeklyBackupsFromSlackAdmin(nowDate)
            ret = weeklyBackup(nowDate)
            msg = 'Weekly backup and deletion of the Database File successfully stored under `'+ret['weeklyStoredAtServer']+'` and sent to '+', '.join(ret['weeklySentToUsers'])+' .'

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
                    slack_SendMsg('The weekly backup and deletion of the Database failed!', user=u)
                print('Weekly Backup failed. Slack Message sent.')
            except:
                print('Failing to send Slack Message with Fail Notice of database weekly backup and deletion.')



    # Delete Products in the shopping list older than 7 days
    print('Delete products in personal shopping list older than 7 days.')
    try:
        deleteTooOldProductsInShoppingList(nowDate)
        print('Finished deletion of products in the shopping list, older than 7 days.')
    except:
        # Send failure message to all admins
        data = KioskUser.objects.filter(visible=True, rechte='Admin')
        try:
            for u in data:
                slack_SendMsg('The deletion of products in the shopping list, older than 7 days, did not complete!', user=u)
            print('Daily deletion of products in the shopping list, older than 7 days failed. Slack Message sent.')
        except:
            print('Failing to send Slack Message with Fail Notice of Daily deletion of products in the shopping list, older than 7 days.')

    

    # Give a warning message to buyers with products in personal shopping list older than 4 days
    print('Do the daily warning of products in the shopping list, older than 4 days.')
    try:
        warningTooOldProductsInShoppingList()
        print('Finished warning of products in the shopping list, older than 4 days.')
    except:
        # Send failure message to all admins
        data = KioskUser.objects.filter(visible=True, rechte='Admin')
        try:
            for u in data:
                slack_SendMsg('The notification of products in the shopping list, older than 4 days, did not complete!', user=u)
            print('Daily warning of products in the shopping list, older than 4 days failed. Slack Message sent.')
        except:
            print('Failing to send Slack Message with Fail Notice of Daily warning of products in the shopping list, older than 4 days.')
    


    # Check, if Users are going to be blocked, give notice to them
    print('Check, if Users are going to be blocked, give notice to them.')
    try:
        warnUsersToBeBlockedSoon()
        print('Finished checking, if Users are going to be blocked, give notice to them.')
    except:
        # Send failure message to all admins
        data = KioskUser.objects.filter(visible=True, rechte='Admin')
        try:
            for u in data:
                slack_SendMsg('The notification of users to be blocked soon, did not complete!', user=u)
            print('Daily warning of users to be blocked soon failed. Slack Message sent.')
        except:
            print('Failing to send Slack Message with Fail Notice of users to be blocked soon.')


    # Block user after active time
    print('Block user after active time.')
    try:
        blockUserAfterActiveTime(nowDate)
        print('Finished blocking user after active time.')
    except:
        # Send failure message to all admins
        data = KioskUser.objects.filter(visible=True, rechte='Admin')
        try:
            for u in data:
                slack_SendMsg('The notification of users to be blocked after active time, did not complete!', user=u)
            print('Daily warning of users to be blocked after active time failed. Slack Message sent.')
        except:
            print('Failing to send Slack Message with Fail Notice of users to be blocked.')


    # Unpersonalise accounts one month after inactivity


    # Weekly: Delete the old history of slackbot messages to the admins with the database save older than 1 year
    

    # Weekly: Check for inactive users and to be deleted ones, check for some constraints: Too high / too low account. Calculate integrity of account, and transactions, and...
