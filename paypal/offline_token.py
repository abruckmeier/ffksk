"""
This script needs to run on a machine with a browser to obtain a token to access gmail.
The token must then be stored on the server.
"""

import os.path
from os import PathLike
from google_auth_oauthlib.flow import InstalledAppFlow


def obtain_token(
        client_secret_file_path: str | PathLike = 'credentials.json',
        scopes: list[str] | str = "https://mail.google.com/",
        local_server_port: int = 8081
) -> bool:
    """
    Obtain a token to access Gmail.
    The token will be saved in a file named "token.json" into the same folder.
    This file must then be uploaded to the server.

    :param client_secret_file_path: Path to the client secret file (default: 'credentials.json').
    :param scopes: Scopes for the token (default: "https://mail.google.com/"). A list can be passed, too.
    :param local_server_port: Port for the local server to run (default: 8081).
    :return: True if the token was successfully obtained and saved.
    """

    if isinstance(scopes, str):
        scopes = [scopes]

    if os.path.exists("token.json"):
        raise Exception('"token.json" already exists. Please delete it before running this script again.')

    flow = InstalledAppFlow.from_client_secrets_file(
        client_secret_file_path, scopes
    )
    creds = flow.run_local_server(port=local_server_port)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    return True
