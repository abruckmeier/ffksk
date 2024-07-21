from imapclient import IMAPClient
from imapclient.response_types import Envelope
from typing import List, TypedDict
import re
from django.conf import settings
from datetime import datetime, timedelta, date
import locale
from paypal.models import Mail
from profil.models import KioskUser
from kiosk.models import GeldTransaktionen


class DownloadedMail(TypedDict):
    """Attributes that are extracted from mails on the server"""
    message_id: int
    flags: tuple
    envelope: Envelope
    data: str


class ExtractedMail(TypedDict):
    """Attributes that are extracted from downloaded mails"""
    downloaded_mail: DownloadedMail
    extraction_was_successful: bool
    user: str | None
    transaction_code: str | None
    transaction_date: date | None
    amount: int | None  # in Eurocent values


def get_recent_mails(ts_since: datetime) -> List[DownloadedMail]:
    """Get mails from PayPal since the given timestamp and return list of downloaded mails for further processing."""

    mails = []

    server = IMAPClient(host=settings.IMAP_HOST, ssl=True)
    server.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
    server.select_folder('INBOX')
    messages = server.search(['FROM', settings.IMAP_SEARCH_FROM_EMAIL,
                              'SINCE', ts_since])
    response = server.fetch(messages, ['FLAGS', 'ENVELOPE', 'RFC822'])
    for message_id, data in response.items():
        mails.append(DownloadedMail(
            message_id=message_id, flags=data[b'FLAGS'],
            envelope=data[b'ENVELOPE'], data=data[b'RFC822'].decode())
        )

    server.logout()
    return mails


def extract_details_from_mail(mail: DownloadedMail) -> ExtractedMail:
    """Extract details from a downloaded mail."""

    extraction_was_successful = True
    txt = mail.get('data')

    usr = re.findall(r'<span>Mitteilung von (?P<usr>[\w\s]+):', txt)
    if len(usr) == 0:
        extraction_was_successful = False
        usr = None
    else:
        usr = usr[0]

    t_code = re.findall(r'<td[\w\W]+?Transaktio[\w\W]*?nscode[\w\W]+?><span>(?P<code>\w+)<\/span><\/a><\/td>',
                        txt)
    if len(t_code) == 0:
        extraction_was_successful = False
        t_code = None
    else:
        t_code = t_code[0]

    t_datum = re.findall(
        r'<span><strong>Transakti[\w\W]*?onsdatum</strong></span><br><span>(?P<t_date>\d+\. \w+ \d+)</span>',
        txt,
    )
    if len(t_datum) == 0:
        extraction_was_successful = False
        t_date = None
    else:
        t_date = t_datum[0]
        try:
            locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
            t_date = datetime.strptime(t_datum[0], '%d. %B %Y').date()
        except Exception:
            extraction_was_successful = False
            t_date = None

    amount = re.findall(r'<strong>Erhaltener Betrag<\/strong>[\w\W]*?>(?P<amount>\d+,\d+)[\w\W]*?EUR<\/td>', txt)
    if len(amount) == 0:
        extraction_was_successful = False
        amount = None
    else:
        amount = amount[0]
        try:
            locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
            amount = int(locale.atof(amount) * 100)
        except Exception:
            extraction_was_successful = False
            amount = None

    return ExtractedMail(
        downloaded_mail=mail,
        extraction_was_successful=extraction_was_successful,
        user=usr,
        transaction_code=t_code,
        transaction_date=t_date,
        amount=amount,
    )


def store_mails_in_db(extracted_mails: List[ExtractedMail]) -> List[Mail]:
    """Store the mails in the database without further processing and return objects"""
    mail_objects = []
    for _mail in extracted_mails:
        mail_objects.append(Mail(
            message_id=_mail.get('downloaded_mail').get('message_id'),
            envelope_str=str(_mail.get('downloaded_mail').get('envelope')),
            mail_ts=_mail.get('downloaded_mail').get('envelope').date,
            data=_mail.get('downloaded_mail').get('data'),
            extraction_was_successful=_mail.get('extraction_was_successful'),
            user_str=_mail.get('user'),
            transaction_code=_mail.get('transaction_code'),
            transaction_date=_mail.get('transaction_date'),
            amount=_mail.get('amount'),
        ))
    return Mail.objects.bulk_create(mail_objects)


def assign_user_and_conduct_transaction(obj: Mail) -> None:
    """"""
    assigned_user: KioskUser | None = KioskUser.objects.filter(
        paypal_name__iexact=obj.user_str
    ).first()
    if not assigned_user:
        return None
    obj.user = assigned_user
    obj.assignment_was_successful = True

    transaction = GeldTransaktionen(
        vonnutzer=KioskUser.objects.get(username='Bargeld'),
        zunutzer=assigned_user,
        betrag=obj.amount,
        kommentar=f'Automatisch generierte Einzahlung nach PayPal-Überweisung. PayPal-Transaktions-Code: {obj.transaction_code}',
    )
    transaction.save()
    obj.geld_transaktion = transaction
    obj.save()

    return None


if __name__ == '__main__':
    # Get the timestamp of the last mail, received. Gather mails from this timestamp up to now
    ts_since = datetime.now() - timedelta(days=7)

    # Get the recent mails from the server
    mails: List[DownloadedMail] = get_recent_mails(ts_since=ts_since)

    # Find out if the mail contains necessary information
    extracted_mails: List[ExtractedMail] = [extract_details_from_mail(_mail) for _mail in mails]

    # Store the mails in the database
    objs = store_mails_in_db(extracted_mails)

    # Check if users can be assigned. Conduct transactions or give notice to admin on failure for mails

