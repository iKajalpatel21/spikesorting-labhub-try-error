import os
import sys
import sqlite3
from pathlib import Path

from passlib.hash import sha512_crypt

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

# BASE_DIR = project root (two levels up from this file: labhub/backends.py → labhub/ → project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
NAS_DB_PATH = os.environ.get("NAS_DB_PATH", str(_PROJECT_ROOT / "NAS_Database" / "freenas-v1.db"))


def _get_nas_admin_credentials():
    """
    Read admin credentials from the NAS database.
    Called once at startup — raises SystemExit (fatal) if the db is unreachable.
    """
    try:
        conn = sqlite3.connect(f"file:{NAS_DB_PATH}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT bsdusr_username, bsdusr_unixhash " "FROM account_bsdusers LIMIT 1"
        )
        result = cursor.fetchone()
        conn.close()
        if not result:
            print(
                f"FATAL: NAS database at {NAS_DB_PATH} has no admin users.",
                file=sys.stderr,
            )
            sys.exit(1)
        return result
    except sqlite3.OperationalError as e:
        print(
            f"FATAL: Cannot read admin credentials from NAS database "
            f"at {NAS_DB_PATH}: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


# Fail fast at import time if the NAS db is not accessible
_get_nas_admin_credentials()


class FreeNASBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            conn = sqlite3.connect(f"file:{NAS_DB_PATH}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT bsdusr_username, bsdusr_unixhash "
                "FROM account_bsdusers "
                "WHERE bsdusr_username=? OR bsdusr_email=?",
                (username, username),
            )
            result = cursor.fetchone()
            conn.close()
        except sqlite3.OperationalError as e:
            print(f"NAS database error during authentication: {e}", file=sys.stderr)
            return None

        if result is None:
            return None

        db_username, db_password_hash = result
        if not sha512_crypt.verify(password, db_password_hash):
            return None

        try:
            user = User.objects.get(username=db_username)
        except ObjectDoesNotExist:
            user = User(username=db_username)
            user.set_unusable_password()
            user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return None
