#!/usr/bin/env python
import os
import sys
import django
import logging

if __name__ == '__main__':
    # Setup the Django environment of the Kiosk
    BASE = os.path.dirname(os.path.dirname(os.path.dirname((os.path.abspath(__file__)))))
    sys.path.append(BASE)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ffeKiosk.settings")
    django.setup()


# Import the Modules
from django.db.models import Q
from datetime import datetime, timedelta, UTC
import pytz
from slack_sdk import WebClient
import time
from io import BytesIO
from utils.slack import get_user_information
from kiosk.queries import readFromDatabase
from kiosk.bot import slack_send_msg, checkKioskContentAndFillUp
from profil.models import KioskUser
from kiosk.models import ZumEinkaufVorgemerkt, GeldTransaktionen
from paypal.paypal_mail import routine_with_messaging
from io import StringIO
from django.core.management import call_command
from django.conf import settings
from cryptography.fernet import Fernet
import gzip

logger = logging.getLogger(__name__)


def run_paypal_sync():
    """Run routine to get the PayPal-Mails and conduct the transactions for the Einzahlung. Response via Slack."""
    is_success, response_msg, _ = routine_with_messaging()
    if is_success:
        # Send message to all admins. If no success, message is already sent in function before.
        admins = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        for u in admins:
            slack_send_msg(response_msg, user=u)


def send_paypal_statistics():
    """"""
    pass


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
        addressaten = ', '.join(['<@'+x+'>' for x in list(set(addressaten))])
        msg = addressaten + chr(10)
        msg += '*Zeit f'+chr(252)+'r ein Lob:*'+chr(10)+chr(10)
        if bestBuyers:
            msg += ':trophy:\tGek'+chr(252)+'rt zum besten Eink'+chr(228)+'ufer dieser Woche wird '+bestBuyers+'!'+chr(10)
        if bestAdmins:
            msg += ':trophy:\tDer flei'+chr(223)+'igste Verwalter war diese Woche '+bestAdmins+'!'+chr(10)

        msg += chr(10)+'Vielen Dank f'+chr(252)+'r Deine Mithilfe im Kiosk!'

        slack_send_msg(msg, to_standard_channel=True)

    return


# Conduct the daily rotating Save of the Database (to local filesystem)
def conduct_backup(nowDate):

    # Get information and stop if not activated
    backupSettings = getattr(settings, 'BACKUP')
    if not backupSettings['active_local_backup'] and not backupSettings['active_slack_backup']:
        logger.info('Backup not activated in settings. Stop.')
        return 'Backup not activated in settings.'

    # Conduct backup via dumpdata and encrypt it
    logger.info('Starting backup via dumpdata...')
    f = Fernet(settings.BACKUP_FILE_SYMMETRIC_KEY)

    buffer = StringIO()
    call_command('dumpdata', '--all', stdout=buffer)
    buffer.seek(0)
    logger.info('Backupd finished. Now encrypting the data...')

    buffer_enc = BytesIO()
    buffer_enc.write(f.encrypt(buffer.read().encode('utf-8')))
    buffer_enc.seek(0)
    logger.info('Data encrypted. Now writing to file and/or to Slack...')

    buffer_gz = BytesIO()
    with gzip.GzipFile(fileobj=buffer_gz, mode='wb') as gzip_file:
        gzip_file.write(buffer_enc.getvalue())
    buffer_gz.seek(0)

    # Create the day-specific file name of the backup file
    attDatabaseName = 'save_' + datetime.strftime(nowDate, '%Y-%m-%dT%H-%M-%S-%fZ') + '.gz'
    backupFolder = backupSettings['localBackupFolder']

    # Store the backup locally
    if backupSettings['active_local_backup']:
        logger.info('Store the backup locally')
        # Get the backup folder
        if not os.path.exists(backupFolder):
            logger.info('Backup Folder does not exist. Create it...')
            os.makedirs(backupFolder)

        # Copy the file to the destination
        with open(os.path.join(backupFolder, attDatabaseName), 'wb') as f:
            f.write(buffer_gz.getvalue())

    # Send the database attached as Slack-message
    if backupSettings['active_slack_backup']:
        logger.info(f'Store the data as Slack message to those users: {backupSettings["sendBackupToUsers"]}')
        slack_token = getattr(settings, 'SLACK_O_AUTH_TOKEN')
        sc = WebClient(slack_token)

        for usr in backupSettings['sendBackupToUsers']:
            logger.info(f'Now, write to Slack user {usr}')

            error, user_address, return_msg = get_user_information(usr)
            if error:
                logger.warning(f'Slack user not found on Slack. Skipping to send file.')
                continue

            # Get the conversation channel for the user-Kioskbot interaction
            channel_resp = sc.conversations_open(users=user_address)

            # Upload the file
            ret = sc.files_upload_v2(
                channel=channel_resp.get('channel').get('id'),
                filename=attDatabaseName,
                file=buffer_gz,
            )
            logger.info(f'Done sending message. Return value: {ret}')

            # Send additional message to the receivers of the attached database
            slack_send_msg(
                'You received the database attached as backup in an other message to the kioskbot. Do not '
                'save the file otherwise! This file will be deleted in one year from the thread.', user=usr)

    return {
        'weeklyStoredAtServer': str(os.path.join(backupFolder, attDatabaseName)) if backupSettings[
            'active_local_backup'] else 'Not activated',
        'weeklySentToUsers': ['@' + x for x in backupSettings['sendBackupToUsers']] if backupSettings[
            'active_slack_backup'] else ['Not activated'],
    }


#
def deleteOldWeeklyBackupsFromSlackAdmin(nowDate):

    # Unix Epoche of timestamp two months before
    dt = (nowDate - timedelta(days=90) - datetime(1970,1,1,tzinfo=pytz.utc)).total_seconds()

    # Get information and stop if not activated
    backupSettings = getattr(settings,'BACKUP')
    if not backupSettings['active_slack_backup']:
        print('Slack Backup not activated in settings. Stop.')
        return 'Slack Backup not activated in settings.'

    slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
    sc = WebClient(slack_token)

    for usr in backupSettings['sendBackupToUsers']:
        logger.info(f'Now, delete old messages in conversation with Slack user {usr}')

        error, user_address, return_msg = get_user_information(usr)
        if error:
            logger.warning(f'Slack user not found on Slack. Skipping to delete files.')
            continue

        # Get the conversation channel for the user-Kioskbot interaction
        channel_resp = sc.conversations_open(users=user_address)
        channel = channel_resp.get('channel').get('id')

        # Delete the file
        conversation = sc.conversations_history(
            channel=channel,
        )

        if not conversation.get('ok', False):
            print('deleteOldWeeklyBackupsFromSlackAdmin: For conversation {}, no messages found.'.format(channel))

        to_delete_msgs = [ msg.get('ts') for msg in conversation.get('messages',[]) if float(msg.get('ts')) < dt  ]

        print('Deletion of following {} messages:'.format(str(len(to_delete_msgs))))
        for ts in to_delete_msgs:
            ret = sc.chat_delete(
                channel=channel,
                ts=ts,
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
        slack_send_msg(msg, u)

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

        slack_send_msg(msg, user=u)

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
        slack_send_msg(msgSend, user=user)

        # Set the flag that user has been warned
        user.activity_end_msg = 1
        user.save()

    return


# Block user after active time
def blockUserAfterActiveTime(nowDate):
    t = nowDate + timedelta(days=1)
    users = KioskUser.objects.filter(aktivBis__lt=t, visible=True, is_active=True, activity_end_msg=1,
        is_functional_user=False,)

    msg = 'Liebe*r Kiosknutzer*in,\nHeute endet dein Besch'+chr(228)+'ftiungsverh'+chr(228)+'ltnis an der FfE und somit auch deine Aktivit'+chr(228)+'t im FfE-Kiosk. Dein Account ist nun inaktiv gesetzt, du kannst also keine Eink'+chr(228)+'ufe mehr t'+chr(228)+'tigen.\nHattest du noch Guthaben auf deinem Konto? Dann lasse dir dies von einem Verwalter ausbezahlen.\n Du verl'+chr(228)+'sst die FfE noch gar nicht? Dann reaktiviere dein Konto unter https://ffekiosk.pythonanywhere.com/accounts/angestellt_bis_change/.\nIn einem Monat werden deine personenbezogenen Daten gel'+chr(246)+'scht, danach ist eine Reaktivierung nicht mehr m'+chr(246)+'glich.\n\nDanke, dass du den FfE-Kiosk genutzt hast!\nDein Kiosk-Team'

    for u in users:

        msgSend = msg
        slack_send_msg(msgSend, user=u)

        # Set status, that message has been sent
        u.activity_end_msg = 2

        # Make user inactive and invisible
        u.visible = False
        u.is_active = False

        u.save()
    return



# Message to inactive users before transferring money and deleting account
def warnInactiveUsersBeforeDeletion(nowDate):

    t = nowDate - timedelta(days=28)
    users = KioskUser.objects.filter(
        aktivBis__lt= t,
        visible= False,
        is_active= False,
        activity_end_msg= 2,
        is_functional_user=False,
    ).filter(
        ~Q(username__in= ('kioskAdmin','Bargeld','Bank','Dieb','Bargeld_Dieb','Bargeld_im_Tresor','Spendenkonto', 'PayPal_Bargeld'),),
    )

    for u in users:
        msg = f'Liebe*r Kiosknuter*in,\nDein Account wurde vor 28 Tagen inaktiv gesetzt. In sieben Tagen wird dein Account endgültig gelöscht{ "und dein verbleibendes Guthaben von "+str(u.kontostand.stand/100)+" "+chr(8364)+" geht als Spende an den Kiosk" if u.kontostand.stand>0 else "" }. Falls du dies nicht möchtest, trete bitte mit einem Administrator in Kontakt.\n\nDanke, dass du den FfE-Kiosk genutzt hast!\nDein Kiosk-Team'

        slack_send_msg(msg, user=u, force_send_to_nonvisible_user=True);print(u)

        # Set status, that message has been sent
        u.activity_end_msg = 3

        u.save()



# Transfer money of inactive user and pseudonymisation
def deleteInactiveUser(nowDate):

    t = nowDate - timedelta(days=35)
    users = KioskUser.objects.filter(
        aktivBis__lt= t,
        visible= False,
        is_active= False,
        activity_end_msg= 3,
        is_functional_user=False,
    ).filter(
        ~Q(username__in= ('kioskAdmin','Bargeld','Bank','Dieb','Bargeld_Dieb','Bargeld_im_Tresor','Spendenkonto', 'PayPal_Bargeld'),),
    )


    bank = KioskUser.objects.get(username='Bank')

    for u in users:

        GeldTransaktionen.doTransaction(vonnutzer=u, zunutzer=bank,
            betrag=u.kontostand.stand, datum=nowDate, kommentar='Transfer of remaining money before deletion of account.')

        u.username = f'deletedUser_{str(u.id)}'
        u.first_name = 'deleted'
        u.last_name = 'deleted'
        u.slackName = f'deletedUser_{str(u.id)}'
        u.activity_end_msg = 4
        u.save()


def routine():

    nowDate = datetime.now(UTC)
    logger.info(f'Start the daily routine with timestamp {nowDate}.')

    # PayPal sync
    logger.info('Do the daily sync of PayPal transactions with the Einzahlung transaction.')
    try:
        run_paypal_sync()
        logger.info('Finished the daily PayPal Sync.')

    except:
        # Send failure message to all admins
        data = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        try:
            for u in data:
                slack_send_msg('The daily PayPal Sync has failed!', user=u)
            logger.info('Daily PayPal Sync failed. Slack Message sent.')
        except:
            logger.info('Failing to send Slack Message with Fail Notice of PayPal daily sync.')


    # Elect best buyers and administrators on Friday
    if nowDate.weekday()==4:
        logger.info('It''s Friday. Elect best buyers and administrators.')
        try:
            electBestContributors()
            logger.info('Done electing best buyers and administrators.')
        except:
            logger.info('Error on posting the best buyers and administrators.')


    # Conduct a daily Backup of the database: Send via Slack to the Admins
    # Furthermore, delete old weekly backups from the conversation
    logger.info('Do the daily backup.')
    try:
        ret = conduct_backup(nowDate)
        logger.info('Daily Backup finished.')

        logger.info('Start deleting old backups from Slack...')
        deleteOldWeeklyBackupsFromSlackAdmin(nowDate)
        logger.info('Done deleting old backups.')

        msg = 'Daily backup and deletion of the Database File successfully stored under `'+ret['weeklyStoredAtServer']+'` and sent to '+', '.join(ret['weeklySentToUsers'])+' .'

        # Send message to all admins
        data = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        for u in data:
            slack_send_msg(msg, user=u)

        logger.info('Finished the weekly backup.')

    except Exception as e:
        logger.exception(e)
        # Send failure message to all admins
        data = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        try:
            for u in data:
                slack_send_msg('The daily backup and deletion of the Database failed!', user=u)
            logger.info('Daily Backup failed. Slack Message sent.')
        except:
            logger.info('Failing to send Slack Message with Fail Notice of database daily backup and deletion.')



    # Delete Products in the shopping list older than 7 days
    print('Delete products in personal shopping list older than 7 days.')
    try:
        deleteTooOldProductsInShoppingList(nowDate)
        print('Finished deletion of products in the shopping list, older than 7 days.')
    except:
        # Send failure message to all admins
        data = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        try:
            for u in data:
                slack_send_msg('The deletion of products in the shopping list, older than 7 days, did not complete!', user=u)
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
        data = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        try:
            for u in data:
                slack_send_msg('The notification of products in the shopping list, older than 4 days, did not complete!', user=u)
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
        data = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        try:
            for u in data:
                slack_send_msg('The notification of users to be blocked soon, did not complete!', user=u)
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
        data = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        try:
            for u in data:
                slack_send_msg('The notification of users to be blocked after active time, did not complete!', user=u)
            print('Daily warning of users to be blocked after active time failed. Slack Message sent.')
        except:
            print('Failing to send Slack Message with Fail Notice of users to be blocked.')


    # Unpersonalise accounts one month after inactivity
    print('Message to inactive users to warn for deletion of account + Deletion of account')
    try:
        warnInactiveUsersBeforeDeletion(nowDate)
        deleteInactiveUser(nowDate)
    except:
        # Send failure message to all admins
        data = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        try:
            for u in data:
                slack_send_msg('Warning and deletion of inactive users, did not complete!', user=u)
            print('Warning and deletion of inactive users failed. Slack Message sent.')
        except:
            print('Failing to send Slack Message with Fail Notice of Warning and deletion of inactive users.')

    # Weekly: Check for inactive users and to be deleted ones, check for some constraints: Too high / too low account. Calculate integrity of account, and transactions, and...


if __name__ == '__main__':
    routine()
