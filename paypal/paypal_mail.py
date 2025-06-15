import base64
import json

from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.utils import parsedate_to_datetime
from imapclient.response_types import Envelope
from typing import List, TypedDict, Tuple
import re
from django.conf import settings
from datetime import datetime, timedelta
from kiosk.bot import slack_send_msg, slack_PostTransactionInformation
from paypal.models import Mail
from profil.models import KioskUser
from kiosk.models import GeldTransaktionen
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class DownloadedMail(TypedDict):
    """Attributes that are extracted from mails on the server"""
    message_id: str
    flags: tuple
    envelope: Envelope
    data: str


class ExtractedMail(TypedDict):
    """Attributes that are extracted from downloaded mails"""
    downloaded_mail: DownloadedMail
    extraction_was_successful: bool
    user: str | None
    transaction_code: str | None
    amount: int | None  # in Eurocent values
    notice: str | None


class MailAssignmentResponse(TypedDict):
    """Response from assignment of user and conduction of transaction,
    with details on the success."""
    mail_obj: Mail
    success: bool
    reason: str


def gmail_to_envelope(gmail_msg):
    """Convert a Gmail message to an Envelope object."""
    headers = {h['name']: h['value'] for h in gmail_msg['payload']['headers']}
    subject = headers.get('Subject', '')
    from_ = headers.get('From', '')
    to = headers.get('To', '')
    date = parsedate_to_datetime(headers.get('Date', ''))
    message_id = headers.get('Message-ID', '')
    in_reply_to = headers.get('In-Reply-To', '')
    cc = headers.get('Cc', '')
    bcc = headers.get('Bcc', '')

    # Envelope erwartet Adresslisten als Tupel von Tupeln (name, email)
    def parse_addr(addr):
        # Hier ggf. mit email.utils.parseaddr oder getaddresses arbeiten
        return ((None, addr),) if addr else ()

    envelope = Envelope(
        date=date,
        subject=subject.encode('utf-8'),
        from_=parse_addr(from_),
        sender=parse_addr(from_),
        reply_to=parse_addr(from_),
        to=parse_addr(to),
        cc=parse_addr(cc),
        bcc=parse_addr(bcc),
        in_reply_to=in_reply_to.encode('utf-8') if in_reply_to else None,
        message_id=message_id.encode('utf-8') if message_id else None,
    )
    return envelope


class CredentialsError(Exception):
    pass


def get_recent_mails(ts_since: datetime) -> List[DownloadedMail]:
    """
    Get mails from PayPal since the given timestamp and return list of downloaded mails for further processing.
    If the token.json file is not found, or the token has expired, an exception is raised.
    With that exception, the login to GMail can be triggered. (FileNotFoundError, CredentialsError, RefreshError)
    """

    mails = []

    try:
        with open('token.json', 'r') as token_file:
            oauth_token = json.loads(token_file.read())
    except FileNotFoundError:
        raise FileNotFoundError('The token.json file is missing. Please run the offline_token.py script to obtain it. Or follow the login sequence.')

    try:
        creds = Credentials.from_authorized_user_info(info=oauth_token,
                                                  scopes=settings.OAUTH_SCOPES)
    except CredentialsError as e:
        raise CredentialsError(f'Error loading credentials to class: {e}')

    service = build('gmail', 'v1', credentials=creds)

    try:
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            q=f'{"from:" + settings.IMAP_SEARCH_FROM_EMAIL + " " if settings.IMAP_SEARCH_FROM_EMAIL else ""}'
              f'after:{int(ts_since.timestamp())}',
            maxResults=100,
        ).execute()
    except RefreshError as e:
        raise CredentialsError(f'Error refreshing credentials: {e}')

    for message in results.get('messages', []):
        # Get the full message details
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        envelope = gmail_to_envelope(msg)

        # Decode the body data if available
        body_data = msg['payload'].get('body', {}).get('data')
        if body_data:
            data = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        else:
            data = ''

        mails.append(DownloadedMail(
            message_id=msg['id'],
            flags=tuple(msg.get('labelIds', [])),
            envelope=envelope,
            data=data,
        ))

    return mails


def extract_details_from_mail(mail: DownloadedMail) -> ExtractedMail:
    """Extract details from a downloaded mail."""

    extraction_was_successful = True
    txt = mail.get('data')
    txt = re.sub(r'=\r\n', '', txt)

    usr = re.findall(r'<strong>Mitteilung von (?P<usr>[\w\s]+)</strong>', txt)
    if len(usr) == 0:
        extraction_was_successful = False
        usr = None
    else:
        usr = usr[0]

    t_code = re.findall(r'<td[\w\W]+?Transaktionscode[\w\W]+?><span>(?P<code>\w+)<\/span><\/a><\/td>',
                        txt)
    if len(t_code) == 0:
        extraction_was_successful = False
        t_code = None
    else:
        t_code = t_code[0]

    amount = re.findall(r'<strong>Erhaltener Betrag<\/strong>[\w\W]*?>(?P<amount_1>\d+)[\w\W]*?,(?P<amount_2>\d+)[\w\W]*?EUR<\/td>', txt)
    if len(amount) == 0:
        extraction_was_successful = False
        amount = None
    else:
        amount = amount[0]
        try:
            amount = int(amount[0]) * 100 + int(amount[1])
        except Exception:
            extraction_was_successful = False
            amount = None

    notice = re.findall(
        r'<span>Mitteilung von [\w\W]+?\/quote-marks-left[\w\W]+?<span>(?P<message>[\w\W]+?)<\/span>[\w\W]+?\/quote-marks-right',
        txt,
    )
    if len(notice) == 0:
        extraction_was_successful = False
        notice = None
    else:
        notice = notice[0]

    return ExtractedMail(
        downloaded_mail=mail,
        extraction_was_successful=extraction_was_successful,
        user=usr,
        transaction_code=t_code,
        amount=amount,
        notice=notice,
    )


def store_mails_in_db(extracted_mails: List[ExtractedMail]) -> List[Mail]:
    """Store the mails in the database without further processing and return objects"""
    mail_objects = []
    for _mail in extracted_mails:
        mail_objects.append(Mail(
            message_id=_mail.get('downloaded_mail').get('message_id'),
            envelope_str=str(_mail.get('downloaded_mail').get('envelope')),
            # @todo: Add timezone information to mail_ts
            mail_ts=_mail.get('downloaded_mail').get('envelope').date,
            data=_mail.get('downloaded_mail').get('data'),
            extraction_was_successful=_mail.get('extraction_was_successful'),
            mail_is_processed=False,
            user_str=_mail.get('user'),
            transaction_code=_mail.get('transaction_code'),
            amount=_mail.get('amount'),
            notice=_mail.get('notice'),
        ))
    return Mail.objects.bulk_create(mail_objects)


@transaction.atomic
def assign_user_and_conduct_transaction(obj: Mail) -> MailAssignmentResponse:
    """Given the extracted values from the mail, the name is assigned to
    a user and the transaction is conducted."""

    response = MailAssignmentResponse(
        mail_obj=obj,
        success=False,
        reason='',
    )

    # Return, if assignment already successfully conducted
    if obj.mail_is_processed:
        response['reason'] = 'Mail is marked as already processed'
        return response
    if not obj.extraction_was_successful:
        response['reason'] = 'Extraction was not marked as successful'
        return response
    if obj.assignment_was_successful:
        response['reason'] = 'Mail has already been assigned.'
        return response

    # Check if the notice in the transaction is "Einzahlung". Else, no transaction!
    if not obj.notice or not re.search('Einzahlung', obj.notice, re.IGNORECASE):
        response['reason'] = 'No notice with Einzahlung given.'
        return response

    if not obj.user:
        assigned_user: KioskUser | None = KioskUser.objects.filter(
            paypal_name__iexact=obj.user_str
        ).first()
        if not assigned_user:
            response['reason'] = 'No user could be matched to the given name'
            return response
    else:
        assigned_user: KioskUser = obj.user

    obj.user = assigned_user
    obj.assignment_was_successful = True

    transaction = GeldTransaktionen.doTransaction(
        vonnutzer=KioskUser.objects.get(username='PayPal_Bargeld'),
        zunutzer=assigned_user,
        betrag=obj.amount,
        datum=obj.mail_ts.date(),
        kommentar=f'Automatisch generierte Einzahlung nach PayPal-Überweisung.'
                  f' PayPal-Transaktions-Code: {obj.transaction_code}',
    )
    obj.geld_transaktion = transaction
    obj.save()

    if getattr(settings, 'ACTIVATE_SLACK_INTERACTION'):
        try:
            slack_PostTransactionInformation(dict(
                type='paypal_eingezahlt',
                betrag=transaction.betrag/100.0,
                userFrom=transaction.vonnutzer,
                userTo=transaction.zunutzer,
            ))
        except:
            pass

    response['reason'] = 'Successfully assigned to user and transaction conducted'
    response['success'] = True
    return response


def routine(with_login_redirect: bool = False) -> Tuple[bool, str, HttpResponse | None]:
    """From the last received mail on, search for new mails from PayPal.
    Store the mails in the database, extract relevant values.
    Assign the user to the PayPal transaction and create a Kiosk transaction.
    The routine returns success bool and relevant responses."""

    warn_msg = ''
    logger.info('Starting the routine.')
    # Find the last mail in database and set the timestamp to filter for in the mails
    #   We expect mails to be downloaded more than once and do not consider them later
    last_mail = Mail.objects.all().order_by('-mail_ts').first()
    if not last_mail:
        ts_since = datetime.now() - timedelta(days=365)
        logger.info(f'No last mail: Use timestamp to start {ts_since}')
    else:
        ts_since = last_mail.mail_ts
        logger.info(f'Last Mail: ID {last_mail.id} with timestamp {ts_since}')

    # Get the recent mails from the server
    logger.info(f'Starting to download mails from server with paypal sender...')
    try:
        mails: List[DownloadedMail] = get_recent_mails(ts_since=ts_since)
    except (FileNotFoundError, CredentialsError, RefreshError) as e:
        msg = f'Obtaining mails failed. Maybe due to login error. Error: {e}'
        logger.exception(msg)
        if with_login_redirect:
            return False, msg, HttpResponseRedirect(reverse('gmail_auth_page'))
        else:
            return False, msg, None
    except Exception as e:
        msg = f'Downloading mails failed. Error: {e}'
        logger.exception(msg)
        return False, msg, None
    logger.info(f'... {len(mails)} mails downloaded')

    # Drop mails that are already in the database
    mails_already_in_db = Mail.objects.filter(
        message_id__in=set([_m.get('message_id') for _m in mails])
    ).values_list('message_id', flat=True)
    logger.info(f'Found {len(mails_already_in_db)} mails already in database. '
                f'We drop those now from the list to upload.')
    mails = [_ for _ in mails if _.get('message_id') not in mails_already_in_db]

    # Find out if the mail contains necessary information
    extracted_mails: List[ExtractedMail] = [extract_details_from_mail(_mail) for _mail in mails]
    logger.info(f'{len(extracted_mails)} Mails have been extracted')

    # Store the mails in the database
    objs = store_mails_in_db(extracted_mails)
    logger.info(f'{len(objs)} Mails have been stored in the database.')
    not_successful_extractions = [
        _obj.message_id for _obj in objs if not _obj.extraction_was_successful
    ]
    if not_successful_extractions:
        warn_msg += (f'{len(not_successful_extractions)}/{len(objs)} Mails could not be extracted successfully. '
                     f'Manual verification required.')
        logger.warning(warn_msg)

    # Check if users can be assigned. Conduct transactions or give notice to admin on failure for mails
    responses: List[MailAssignmentResponse] = [
        assign_user_and_conduct_transaction(_obj) for _obj in objs
    ]
    logger.info(f'{len(objs)} database entries have been tried to be assigned to a user, '
                f'and transactions have been tried to be created.')
    failed_assignments = [_ for _ in responses if not _.get('success')]
    if failed_assignments:
        warn_msg_2 = (f'{len(failed_assignments)}/{len(objs)} mails have failed to be assigned to user. '
                      f'No transaction has been created. '
                      f'Manual verification required. Elements shown below.')
        logger.warning(warn_msg_2)
        warn_msg += '\n' + warn_msg_2
        for _assignment in failed_assignments:
            _msg = (f'Message-ID: {_assignment.get("mail_obj").message_id}. '
                    f'Reason {_assignment.get("reason")}.')
            logger.warning(_msg)
            warn_msg += '\n' + _msg

    if not warn_msg:
        return True, f'Successfully saved and assigned {len(objs)} transactions from mails', None
    else:
        return False, f'Saved and assigned {len(objs)} transactions from mails with warnings.\n' + warn_msg, None


def routine_with_messaging(with_login_redirect: bool = False) -> Tuple[bool, str, HttpResponse | None]:
    """Run the routine and send messages to the admins via Slack, only if error occur.
    Return the response of the routine."""
    try:
        # Run routine
        is_success, response_msg, response = routine(
            with_login_redirect=with_login_redirect
        )
        # Slack Message to Admin on Failure
        if not is_success:
            # Send message to all admins
            admins = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
            for u in admins:
                slack_send_msg(response_msg, user=u)
    except Exception as e:
        logger.exception(e)
        response = None
        response_msg = f'An unexpected Exception has occurred: {str(e)}.'
        is_success = False
        # Send message to all admins
        admins = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        for u in admins:
            slack_send_msg(response_msg, user=u)
    return is_success, response_msg, response


if __name__ == '__main__':
    is_success, response_msg, response = routine_with_messaging()
