"""
This script needs to run on a machine with a browser to obtain a token to access gmail.
The token must then be stored on the server.
"""

from os import PathLike

from django.conf import settings
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from google_auth_oauthlib.flow import InstalledAppFlow
import logging

from paypal.models import Token

logger = logging.getLogger(__name__)


def obtain_token(
        client_secret_file_path: str | PathLike = 'credentials.json',
        scopes: list[str] | str = "https://mail.google.com/",
        local_server_port: int = 8081
) -> bool:
    """
    Obtain a token to access Gmail.
    The token will be saved into the database.

    :param client_secret_file_path: Path to the client secret file (default: 'credentials.json').
    :param scopes: Scopes for the token (default: "https://mail.google.com/"). A list can be passed, too.
    :param local_server_port: Port for the local server to run (default: 8081).
    :return: True if the token was successfully obtained and saved.
    """

    if isinstance(scopes, str):
        scopes = [scopes]

    flow = InstalledAppFlow.from_client_secrets_file(
        client_secret_file_path, scopes
    )
    creds = flow.run_local_server(port=local_server_port)
    # Save the credentials for the next run
    token_obj = Token.set_new_token(flow.credentials.to_json())
    return True


def gmail_login_redirect(request: HttpRequest) -> HttpResponseRedirect:
    """
    Redirects the user to the Google OAuth login page to authenticate and authorize access to Gmail and then
    takes the user back to the gmail_auth_response_page where then the token is stored.
    """
    flow = InstalledAppFlow.from_client_config(settings.OAUTH_CREDENTIALS, settings.OAUTH_SCOPES)
    flow.redirect_uri = request.build_absolute_uri(reverse('gmail_auth_response_page'))
    auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
    return HttpResponseRedirect(auth_url)


def gmail_auth_response(request: HttpRequest) -> HttpResponseRedirect | None:
    """
    After the user has logged in into GMail, the user is redirected to this page.
    Here, the token is fetched and saved to the database.
    This is then used for logging in to GMail in the future.
    """

    response_uri = request.build_absolute_uri()
    response_uri = response_uri.replace('http://', 'https://')

    flow = InstalledAppFlow.from_client_config(settings.OAUTH_CREDENTIALS, settings.OAUTH_SCOPES)
    flow.redirect_uri = request.build_absolute_uri(reverse('gmail_auth_response_page'))

    flow.fetch_token(authorization_response=response_uri)

    token_obj = Token.set_new_token(flow.credentials.to_json())

    return
