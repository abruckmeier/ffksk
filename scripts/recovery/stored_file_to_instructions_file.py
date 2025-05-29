"""
The script converts a stored backup file from the scripts.routines.dailyTasks.conduct_backup function
to a file for the recovery process with python manage.py loaddata.

After conversion of the file to a instruction document, the file just needs to be loaded with the command:
python manage.py loaddata loaddata_instructions.json

But before that, some database tables must be cleaned up.
    - auth_group
    - auth_group_permission
    - auth_permission
    - django_content_type
    - django_migrations

"""

import gzip
import io
from os import PathLike
from django.conf import settings
from cryptography.fernet import Fernet


def convert_backup_to_instructions_file(file_path: PathLike | str) -> None:
    """
    Convert the stored backup file to a file for the recovery process.
    The file will be saved as 'instructions.json'.
    """

    # Unzip the file
    with gzip.open(file_path, 'rb') as f:
        data = f.read()
    buffer = io.BytesIO(data)

    # Decrypt the file
    f = Fernet(settings.BACKUP_FILE_SYMMETRIC_KEY)
    encrypted_data = buffer.getvalue()
    decrypted_data = f.decrypt(encrypted_data)
    with open('loaddata_instructions.json', 'wb') as out_file:
        out_file.write(decrypted_data)
