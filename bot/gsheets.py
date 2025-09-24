import json
import gspread
from google.oauth2.service_account import Credentials
from typing import Tuple, Optional


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def open_sheet_by_url(credentials_path: str, sheet_url: str):
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_url(sheet_url)
    return sh


def check_access(credentials_path: str, sheet_url: str) -> Tuple[bool, str, Optional[str]]:
    try:
        sh = open_sheet_by_url(credentials_path, sheet_url)
        # простая проверка — читаем имена листов
        _ = [ws.title for ws in sh.worksheets()]
        return True, "ok", sh.title
    except Exception as e:
        return False, str(e), None

